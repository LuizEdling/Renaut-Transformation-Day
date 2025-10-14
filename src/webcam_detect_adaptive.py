import cv2
from ultralytics import YOLO
import numpy as np
import time
from collections import defaultdict
from cube_time_logger import create_logger

class CubeDetector:
    def __init__(self, model_path):
        """Inicializa o detector de cubos com tracking por cor"""
        self.model = YOLO(model_path)
        self.confidence = 0.5
        
        # Mapeamento de cores para faces do cubo magico
        self.color_mapping = {
            'white': 'Frente',
            'yellow': 'Atras', 
            'red': 'Encima',
            'orange': 'Embaixo',
            'blue': 'Direita',
            'green': 'Esquerda'
        }
        
        # Ranges de cores em HSV melhorados para deteccao mais precisa
        self.color_ranges = {
            'white': ([0, 0, 200], [180, 50, 255]),  # Ajustado: saturacao ate 50, valor minimo 200
            'yellow': ([20, 100, 100], [30, 255, 255]),
            'red': ([0, 100, 100], [10, 255, 255]),
            'red2': ([170, 100, 100], [180, 255, 255]),
            'orange': ([10, 100, 100], [20, 255, 255]),
            'blue': ([100, 80, 80], [130, 255, 255]),  # Ajustado: saturacao e valor minimos reduzidos
            'green': ([40, 100, 100], [80, 255, 255])
        }
        
        # Sistema de tracking por cor - cada cor e um cubo diferente
        self.active_cubes_by_color = {}  # {color: cube_data}
        self.cube_history = []  # Historico de cubos que sairam
        self.color_total_times = defaultdict(float)  # Tempo total por cor
        
        # Parametros de tracking
        self.max_distance_threshold = 120
        self.color_confidence_threshold = 0.15  # Reduzido para melhor deteccao
        self.max_cubes_simultaneous = 6  # Uma para cada cor
        
        # Historico de cores para estabilizacao
        self.color_detection_history = {}  # {color: [detected_colors_list]}
        
        # Parametros de estabilizacao
        self.min_color_samples = 2  # Reduzido para resposta mais rapida
        self.max_color_history = 8  # Reduzido para resposta mais rapida
        self.color_stability_threshold = 0.6  # 60% das deteccoes devem concordar
        
        # Debug - mostra informacoes de deteccao
        self.debug_mode = True
        
    def detect_cube_color(self, frame, bbox):
        """Detecta a cor dominante do cubo com filtros de ruído melhorados"""
        x1, y1, x2, y2 = bbox
        
        # Extrai região do cubo
        roi = frame[y1:y2, x1:x2]
        if roi.size == 0:
            return 'unknown', 0.0
        
        # Aplica filtro gaussiano para reduzir ruído
        roi_blurred = cv2.GaussianBlur(roi, (5, 5), 0)
        
        # Converte para HSV
        hsv = cv2.cvtColor(roi_blurred, cv2.COLOR_BGR2HSV)
        
        # Pega região central (maior área para melhor análise)
        h, w = hsv.shape[:2]
        center_h, center_w = h // 2, w // 2
        center_size = min(h, w) // 2  # Aumentado para melhor detecção
        
        center_roi = hsv[
            max(0, center_h - center_size//2):min(h, center_h + center_size//2),
            max(0, center_w - center_size//2):min(w, center_w + center_size//2)
        ]
        
        if center_roi.size == 0:
            return 'unknown', 0.0
        
        # Aplica morfologia para limpar a máscara
        kernel = np.ones((3,3), np.uint8)
        
        # Testa cada cor com filtros melhorados
        color_scores = {}
        
        for color_name, (lower, upper) in self.color_ranges.items():
            if color_name == 'red2':
                continue
                
            lower = np.array(lower, dtype=np.uint8)
            upper = np.array(upper, dtype=np.uint8)
            
            mask = cv2.inRange(center_roi, lower, upper)
            # Aplica operações morfológicas para limpar ruído
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            
            total_pixels = mask.size
            color_pixels = np.sum(mask > 0)
            percentage = color_pixels / total_pixels if total_pixels > 0 else 0
            
            color_scores[color_name] = percentage
        
        # Trata vermelho especial - combina dois ranges
        red_lower1 = np.array(self.color_ranges['red'][0], dtype=np.uint8)
        red_upper1 = np.array(self.color_ranges['red'][1], dtype=np.uint8)
        red_lower2 = np.array(self.color_ranges['red2'][0], dtype=np.uint8)
        red_upper2 = np.array(self.color_ranges['red2'][1], dtype=np.uint8)
        
        mask1 = cv2.inRange(center_roi, red_lower1, red_upper1)
        mask2 = cv2.inRange(center_roi, red_lower2, red_upper2)
        red_mask = cv2.bitwise_or(mask1, mask2)
        # Aplica morfologia também no vermelho
        red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_CLOSE, kernel)
        red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_OPEN, kernel)
        
        total_pixels = red_mask.size
        red_pixels = np.sum(red_mask > 0)
        color_scores['red'] = red_pixels / total_pixels if total_pixels > 0 else 0
        
        # Encontra melhor cor
        if not color_scores:
            return 'unknown', 0.0
        
        best_color = max(color_scores, key=color_scores.get)
        confidence = color_scores[best_color]
        
        # Debug - mostra informações de detecção (removido para limpar terminal)
        
        # Thresholds específicos por cor para melhor detecção
        color_thresholds = {
            'white': 0.03,  # Threshold mais baixo para branco
            'blue': 0.04,   # Threshold mais baixo para azul
            'red': 0.05,
            'orange': 0.05,
            'yellow': 0.05,
            'green': 0.05
        }
        
        min_threshold = color_thresholds.get(best_color, 0.05)
        
        if confidence < min_threshold:
            return 'unknown', confidence
        
        return best_color, confidence
    
    def test_color_ranges(self, frame, bbox):
        """Função de teste para analisar diferentes ranges de cores"""
        x1, y1, x2, y2 = bbox
        roi = frame[y1:y2, x1:x2]
        if roi.size == 0:
            return
        
        roi_blurred = cv2.GaussianBlur(roi, (5, 5), 0)
        hsv = cv2.cvtColor(roi_blurred, cv2.COLOR_BGR2HSV)
        
        h, w = hsv.shape[:2]
        center_h, center_w = h // 2, w // 2
        center_size = min(h, w) // 2
        
        center_roi = hsv[
            max(0, center_h - center_size//2):min(h, center_h + center_size//2),
            max(0, center_w - center_size//2):min(w, center_w + center_size//2)
        ]
        
        if center_roi.size == 0:
            return
        
        # Testa ranges alternativos para azul e branco
        test_ranges = {
            'white_alt1': ([0, 0, 180], [180, 30, 255]),
            'white_alt2': ([0, 0, 200], [180, 50, 255]),
            'white_alt3': ([0, 0, 160], [180, 60, 255]),
            'blue_alt1': ([100, 60, 60], [130, 255, 255]),
            'blue_alt2': ([100, 80, 80], [130, 255, 255]),
            'blue_alt3': ([95, 50, 50], [135, 255, 255])
        }
        
        # Teste de ranges de cores (removido para limpar terminal)
        for name, (lower, upper) in test_ranges.items():
            lower = np.array(lower, dtype=np.uint8)
            upper = np.array(upper, dtype=np.uint8)
            mask = cv2.inRange(center_roi, lower, upper)
            total_pixels = mask.size
            color_pixels = np.sum(mask > 0)
            percentage = color_pixels / total_pixels if total_pixels > 0 else 0
    
    def draw_time_block(self, frame, detector):
        """Desenha um bloco visual destacado com os tempos totais por cor"""
        if not detector.color_total_times:
            return
        
        # Dimensões do bloco
        block_width = 300
        block_height = 200
        block_x = frame.shape[1] - block_width - 20  # 20px da borda direita
        block_y = 20  # 20px do topo
        
        # Desenha fundo do bloco com transparência
        overlay = frame.copy()
        cv2.rectangle(overlay, (block_x, block_y), (block_x + block_width, block_y + block_height), 
                     (0, 0, 0), -1)  # Fundo preto
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        # Borda do bloco
        cv2.rectangle(frame, (block_x, block_y), (block_x + block_width, block_y + block_height), 
                     (255, 255, 255), 2)
        
        # Título do bloco
        title_y = block_y + 25
        cv2.putText(frame, "TEMPOS TOTAIS POR COR", (block_x + 10, title_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Cores para cada linha
        color_colors = {
            'white': (255, 255, 255),
            'yellow': (0, 255, 255),
            'red': (0, 0, 255),
            'orange': (0, 165, 255),
            'blue': (255, 0, 0),
            'green': (0, 255, 0)
        }
        
        # Desenha cada cor com seu tempo total
        y_offset = title_y + 30
        for color, total_time in detector.color_total_times.items():
            face_name = detector.color_mapping.get(color, 'Desconhecida')
            text = f"{color.upper()}: {total_time:.1f}s"
            
            # Cor do texto baseada na cor do cubo
            text_color = color_colors.get(color, (255, 255, 255))
            
            cv2.putText(frame, text, (block_x + 15, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 2)
            y_offset += 25
    
    def calculate_distance(self, bbox1, bbox2):
        """Calcula distância entre centroides de duas bounding boxes"""
        x1_1, y1_1, x2_1, y2_1 = bbox1
        x1_2, y1_2, x2_2, y2_2 = bbox2
        
        center1 = ((x1_1 + x2_1) // 2, (y1_1 + y2_1) // 2)
        center2 = ((x1_2 + x2_2) // 2, (y1_2 + y2_2) // 2)
        
        return np.sqrt((center1[0] - center2[0])**2 + (center1[1] - center2[1])**2)
    
    def get_stable_color(self, cube_id):
        """Retorna a cor mais estável baseada no histórico"""
        if cube_id not in self.color_detection_history or len(self.color_detection_history[cube_id]) < self.min_color_samples:
            return 'unknown', 0.0
        
        # Conta frequência de cada cor no histórico
        color_counts = defaultdict(int)
        for detected_color in self.color_detection_history[cube_id]:
            color_counts[detected_color] += 1
        
        if not color_counts:
            return 'unknown', 0.0
        
        # Retorna a cor mais frequente
        most_common_color = max(color_counts, key=color_counts.get)
        confidence = color_counts[most_common_color] / len(self.color_detection_history[cube_id])
        
        # Só retorna a cor se a confiança for alta o suficiente
        if confidence >= self.color_stability_threshold:
            return most_common_color, confidence
        else:
            return 'unknown', confidence
    
    def update_tracking(self, detections, current_time):
        """Sistema de tracking baseado em cores - cada cor é um cubo diferente"""
        # Marca todos os cubos ativos como não detectados neste frame
        for color in self.active_cubes_by_color:
            self.active_cubes_by_color[color]['detected_this_frame'] = False
        
        # Processa cada detecção
        for detection in detections:
            bbox = detection['bbox']
            
            # Detecta cor da detecção
            cube_color, color_conf = self.detect_cube_color(
                detection.get('frame', None), bbox
            )
            
            if color_conf > self.color_confidence_threshold and cube_color != 'unknown':
                # Verifica se já existe um cubo desta cor
                if cube_color in self.active_cubes_by_color:
                    # Atualiza cubo existente da mesma cor
                    cube = self.active_cubes_by_color[cube_color]
                    cube['bbox'] = bbox
                    cube['last_seen'] = current_time
                    cube['detected_this_frame'] = True
                    
                    # Adiciona cor detectada ao histórico
                    if cube_color not in self.color_detection_history:
                        self.color_detection_history[cube_color] = []
                    
                    self.color_detection_history[cube_color].append(cube_color)
                    
                    # Mantém apenas os últimos valores
                    if len(self.color_detection_history[cube_color]) > self.max_color_history:
                        self.color_detection_history[cube_color] = self.color_detection_history[cube_color][-self.max_color_history:]
                    
                else:
                    # Nova cor detectada - cria novo cubo para esta cor
                    cube_id = f"cubo_{cube_color}_{len(self.active_cubes_by_color) + 1}"
                    self.active_cubes_by_color[cube_color] = {
                        'id': cube_id,
                        'color': cube_color,
                        'entry_time': current_time,
                        'last_seen': current_time,
                        'bbox': bbox,
                        'detected_this_frame': True
                    }
                    
                    # Inicializa histórico de cores
                    self.color_detection_history[cube_color] = [cube_color]
        
        # Remove cubos que não foram detectados neste frame
        cubes_to_remove = []
        for color, cube_data in self.active_cubes_by_color.items():
            if not cube_data['detected_this_frame']:
                cubes_to_remove.append(color)
        
        # Remove cubos e adiciona ao histórico
        for color in cubes_to_remove:
            cube_data = self.active_cubes_by_color[color]
            # Usa o tempo atual (quando o cubo saiu) em vez da última detecção
            total_time = current_time - cube_data['entry_time']
            
            # Adiciona ao tempo total desta cor
            self.color_total_times[color] += total_time
            
            cube_data['total_time'] = total_time
            cube_data['final_color'] = color
            cube_data['total_time_for_color'] = self.color_total_times[color]
            
            self.cube_history.append(cube_data.copy())
            
            # Adiciona ao logger se estiver disponível
            if hasattr(self, 'logger'):
                self.logger.add_cube(color, total_time)
            
            del self.active_cubes_by_color[color]
            # Limpa histórico de cores
            if color in self.color_detection_history:
                del self.color_detection_history[color]
    
    def detect_cubes(self, frame, current_time):
        """Detecta cubos no frame"""
        # Faz predição
        results = self.model(frame, conf=self.confidence, verbose=False)
        
        detections = []
        for r in results:
            if r.boxes is not None:
                for box in r.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    conf = float(box.conf[0])
                    
                    detections.append({
                        'bbox': (x1, y1, x2, y2),
                        'confidence': conf,
                        'frame': frame  # Passa o frame para detecção de cor
                    })
        
        # Atualiza tracking
        self.update_tracking(detections, current_time)
        
        return detections

def main():
    # Carrega o melhor modelo disponível
    model_paths = [
        "runs-cube/yolov8n-cube5/weights/best.pt",
        "runs-cube/yolov8n-cube4/weights/best.pt",
        "runs-cube/yolov8n-cube3/weights/best.pt"
    ]
    
    model_path = None
    for path in model_paths:
        try:
            YOLO(path)
            model_path = path
            break
        except:
            continue
    
    if model_path is None:
        return
    
    # Inicializa detector
    detector = CubeDetector(model_path)
    
    # Inicializa logger
    logger = create_logger()
    detector.logger = logger
    
    # Abre webcam - tenta diferentes câmeras automaticamente
    cap = None
    for camera_id in [1, 0, 2, 3]:  # Tenta câmera 1 primeiro, depois 0, 2, 3...
        cap = cv2.VideoCapture(camera_id)
        if cap.isOpened():
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(cv2.CAP_PROP_FPS, 30)
            break
        else:
            cap.release()
    
    if not cap or not cap.isOpened():
        return
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        current_time = time.time()
        
        # Detecta cubos
        detections = detector.detect_cubes(frame, current_time)
        
        # Desenha detecções para cubos ativos
        for color, cube_data in detector.active_cubes_by_color.items():
            x1, y1, x2, y2 = cube_data['bbox']
            
            # Cor do contorno baseada na cor detectada
            color_map = {
                'white': (255, 255, 255),
                'yellow': (0, 255, 255),
                'red': (0, 0, 255),
                'orange': (0, 165, 255),
                'blue': (255, 0, 0),
                'green': (0, 255, 0),
                'unknown': (128, 128, 128)
            }
            
            color_bgr = color_map.get(color, (128, 128, 128))
            face_name = detector.color_mapping.get(color, 'Desconhecida')
            
            # Desenha contorno
            cv2.rectangle(frame, (x1, y1), (x2, y2), color_bgr, 3)
            
            # Calcula tempo na tela - usa último tempo visto se não foi detectado neste frame
            if cube_data['detected_this_frame']:
                time_in_frame = current_time - cube_data['entry_time']
            else:
                time_in_frame = cube_data['last_seen'] - cube_data['entry_time']
            
            # Texto com tempo e face
            label = f"Cubo {color} | {time_in_frame:.1f}s | {face_name}"
            
            cv2.putText(frame, label, (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color_bgr, 2)
        
        # Bloco de tempos totais por cor - posicionado no canto superior direito
        detector.draw_time_block(frame, detector)
        
        # Informações dos cubos ativos - posicionado no canto superior esquerdo
        y_offset = 30
        if detector.active_cubes_by_color:
            cv2.putText(frame, f"Cubos Ativos: {len(detector.active_cubes_by_color)}", (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            y_offset += 25
            
            for color, cube_data in detector.active_cubes_by_color.items():
                face_name = detector.color_mapping.get(color, 'Desconhecida')
                # Calcula tempo corretamente - para quando nao detectado
                if cube_data['detected_this_frame']:
                    time_in_frame = current_time - cube_data['entry_time']
                else:
                    time_in_frame = cube_data['last_seen'] - cube_data['entry_time']
                
                text = f"Cubo {color}: {time_in_frame:.1f}s | {face_name}"
                
                cv2.putText(frame, text, (10, y_offset),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                y_offset += 20
        
        # Informações do logger
        if hasattr(detector, 'logger'):
            group_info = detector.logger.get_current_group_info()
            y_offset += 10
            cv2.putText(frame, f"Grupo Atual: {group_info['current_group_size']}/3", (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
            y_offset += 20
            
            # Mostra as cores do grupo atual
            if group_info['current_colors']:
                colors_text = f"Cores: {', '.join(group_info['current_colors'])}"
                cv2.putText(frame, colors_text, (10, y_offset),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)
                y_offset += 15
            
            cv2.putText(frame, f"Grupos Finalizados: {group_info['total_groups']}", (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
        
        # Controles na tela
        y_offset += 30
        cv2.putText(frame, "Controles: 'q'=sair, 't'=testar cores, 'd'=debug, 'f'=finalizar grupo", (10, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
        y_offset += 15
        cv2.putText(frame, f"Debug: {'ON' if detector.debug_mode else 'OFF'}", (10, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
        
        # Mostra frame
        cv2.imshow("Detecção de Cubos", frame)
        
        # Controles
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('t'):  # Tecla 't' para testar ranges de cores
            if detections:
                detector.test_color_ranges(frame, detections[0]['bbox'])
        elif key == ord('d'):  # Tecla 'd' para toggle debug
            detector.debug_mode = not detector.debug_mode
        elif key == ord('f'):  # Tecla 'f' para finalizar grupo atual
            if hasattr(detector, 'logger'):
                detector.logger.force_finalize_group()
    
    # Finaliza grupo restante se houver
    if hasattr(detector, 'logger') and detector.logger.current_group:
        detector.logger.force_finalize_group()
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()