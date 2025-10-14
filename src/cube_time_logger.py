import json
import os
from datetime import datetime
from collections import defaultdict

class CubeTimeLogger:
    def __init__(self):
        """Inicializa o logger de tempos dos cubos"""
        # Mapeamento de cores para faces do cubo mágico
        self.color_mapping = {
            'white': 'Frente',
            'yellow': 'Atras', 
            'red': 'Encima',
            'orange': 'Embaixo',
            'blue': 'Direita',
            'green': 'Esquerda'
        }
        
        # Sistema de grupos de 3 cubos
        self.current_group = []  # Grupo atual sendo formado
        self.group_number = 1
        self.all_groups = []  # Todos os grupos finalizados
        
        # Arquivo de log
        self.log_file = f"cube_times_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        self.json_file = f"cube_times_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Logger de tempos iniciado silenciosamente
    
    def add_cube(self, color, individual_time):
        """Adiciona um cubo ao grupo atual (apenas se a cor não existir no grupo)"""
        face_name = self.color_mapping.get(color, 'Desconhecida')
        
        # Verifica se a cor já existe no grupo atual
        existing_colors = [cube['color'] for cube in self.current_group]
        if color in existing_colors:
            return
        
        cube_data = {
            'color': color,
            'face_name': face_name,
            'individual_time': individual_time,
            'timestamp': datetime.now().isoformat()
        }
        
        self.current_group.append(cube_data)
        
        # Verifica se completou um grupo de 3 cores diferentes
        if len(self.current_group) == 3:
            self.finalize_group()
    
    def finalize_group(self):
        """Finaliza um grupo de 3 cubos com cores diferentes e calcula o tempo total"""
        if len(self.current_group) != 3:
            return
        
        # Verifica se todas as cores são diferentes
        colors = [cube['color'] for cube in self.current_group]
        if len(set(colors)) != 3:
            return
        
        # Calcula tempo total do grupo
        group_total_time = sum(cube['individual_time'] for cube in self.current_group)
        
        group_data = {
            'group_number': self.group_number,
            'cubes': self.current_group.copy(),
            'total_group_time': group_total_time,
            'timestamp': datetime.now().isoformat()
        }
        
        # Adiciona aos grupos
        self.all_groups.append(group_data)
        
        # Salva no arquivo
        self.save_to_files()

        # Executa análise de atrasos (única saída no terminal)
        self.analyze_delays()

        # Limpa grupo atual e incrementa número
        self.current_group = []
        self.group_number += 1
    
    def save_to_files(self):
        """Salva os dados nos arquivos de texto e JSON"""
        # Salva em arquivo de texto simples
        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write("=== RELATÓRIO DE TEMPOS DOS CUBOS ===\n")
            f.write(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
            
            for group in self.all_groups:
                f.write(f"GRUPO {group['group_number']}:\n")
                f.write(f"Data/Hora: {group['timestamp']}\n")
                f.write("-" * 40 + "\n")
                
                for i, cube in enumerate(group['cubes'], 1):
                    f.write(f"{i}. Cor: {cube['color'].upper()}\n")
                    f.write(f"   Face: {cube['face_name']}\n")
                    f.write(f"   Tempo: {cube['individual_time']:.1f}s\n\n")
                
                f.write(f"TEMPO TOTAL DO GRUPO: {group['total_group_time']:.1f}s\n")
                f.write("=" * 50 + "\n\n")
        
        # Salva em arquivo JSON para dados estruturados
        json_data = {
            'session_start': datetime.now().isoformat(),
            'groups_of_three': self.all_groups,
            'total_groups': len(self.all_groups)
        }
        
        with open(self.json_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    def get_current_group_info(self):
        """Retorna informações do grupo atual"""
        existing_colors = [cube['color'] for cube in self.current_group]
        return {
            'current_group_size': len(self.current_group),
            'current_group': self.current_group.copy(),
            'current_colors': existing_colors,
            'total_groups': len(self.all_groups)
        }
    
    def force_finalize_group(self):
        """Força a finalização do grupo atual (mesmo que não tenha 3 cubos)"""
        if self.current_group:
            self.finalize_group()
    
    def get_summary(self):
        """Retorna um resumo dos dados"""
        total_cubes = sum(len(group['cubes']) for group in self.all_groups)
        total_time = sum(group['total_group_time'] for group in self.all_groups)
        
        return {
            'total_groups': len(self.all_groups),
            'total_cubes': total_cubes,
            'total_time': total_time,
            'current_group_size': len(self.current_group)
        }

# Função para usar o logger no webcam_detect_adaptive.py

  # -------------------------------
    # ANÁLISE DE DESEMPENHO E ATRASOS
    # -------------------------------
    def analyze_delays(self):
        """
        Analisa o último grupo comparando com a média esperada:
        - Tempo médio por cubo: 5s
        - Tempo médio total: 15s
        Detecta cubos ou grupos adiantados/atrasados em ±5s
        """
        if not self.all_groups:
            return

        expected_cube_time = 5.0       # tempo esperado por cubo (s)
        expected_group_time = 15.0     # tempo esperado por grupo (s)
        tolerance = 5.0                # margem de tolerância (s)

        last_group = self.all_groups[-1]
        total_time = last_group["total_group_time"]

        print("\n=== ANÁLISE DE DESEMPENHO ===")
        print(f"Grupo {last_group['group_number']} - Tempo total: {total_time:.2f}s\n")

        atraso_cubos = []
        adiantados_cubos = []

        # Analisa cubo por cubo
        for cube in last_group["cubes"]:
            tempo = cube["individual_time"]
            cor = cube["color"]
            diferenca = tempo - expected_cube_time
            

            if diferenca > tolerance:
                atraso_cubos.append((cor, tempo, diferenca))
            elif diferenca < -tolerance:
                adiantados_cubos.append((cor, tempo, diferenca))

            print(f"- {cor.upper()}: {tempo:.2f}s (diferença: {diferenca:+.2f}s)")

        # Análise do grupo total
        total_diff = total_time - expected_group_time
        print("\nTempo total esperado: 15.00s")
        print(f"Desvio total do grupo: {total_diff:+.2f}s")

        # Diagnóstico geral
        if total_diff > tolerance:
            print("🚨 O grupo atrasou em relação ao tempo médio!")
            if atraso_cubos:
                print("Causado por:")
                for cor, tempo, dif in atraso_cubos:
                    print(f"  -> {cor.upper()} demorou {dif:+.2f}s a mais ({tempo:.2f}s)")
        elif total_diff < -tolerance:
            print("⚡ O grupo foi mais rápido que o esperado!")
            if adiantados_cubos:
                print("Provavelmente acelerado por:")
                for cor, tempo, dif in adiantados_cubos:
                    print(f"  -> {cor.upper()} foi {dif:+.2f}s mais rápido ({tempo:.2f}s)")
        else:
            print("✅ O grupo está dentro do tempo esperado.")

        print("=" * 50)

def create_logger():
    """Cria uma instância do logger para usar no detector principal"""
    return CubeTimeLogger()

# Exemplo de uso no webcam_detect_adaptive.py:
"""
# No início do arquivo webcam_detect_adaptive.py, adicione:
from cube_time_logger import create_logger

# Na função main(), após criar o detector:
logger = create_logger()

# Quando um cubo sair (na função update_tracking), adicione:
logger.add_cube(color, total_time)

# Para finalizar grupo manualmente, adicione no controle de teclas:
elif key == ord('f'):  # Tecla 'f' para finalizar grupo
    logger.force_finalize_group()
"""
