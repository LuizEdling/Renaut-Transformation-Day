# Detector de Cubos Mágicos Simplificado

Este projeto detecta cubos mágicos em tempo real usando uma webcam, identifica a cor da face voltada para a câmera e calcula o tempo que o cubo fica na tela.

## Funcionalidades

- ✅ Detecção de cubos usando modelo YOLO pré-treinado
- ✅ Identificação de cores das faces (Branco, Amarelo, Vermelho, Laranja, Azul, Verde)
- ✅ Contorno do cubo na cor correspondente à face detectada
- ✅ Cálculo e exibição do tempo que o cubo fica na tela
- ✅ Histórico dos últimos 5 cubos detectados

## Mapeamento de Cores

- **Branco** → Frente
- **Amarelo** → Atrás
- **Vermelho** → Encima
- **Laranja** → Embaixo
- **Azul** → Direita
- **Verde** → Esquerda

## Como Usar

1. Certifique-se de ter o modelo YOLO treinado na pasta `runs-cube/`
2. Execute o script:
   ```bash
   python src/webcam_detect_adaptive.py
   ```
3. Aponte a webcam para um cubo mágico
4. O sistema detectará automaticamente e mostrará:
   - Contorno colorido do cubo
   - Tempo na tela
   - Nome da face detectada
   - Histórico de tempos

## Controles

- **Q**: Sair do programa

## Requisitos

- Python 3.7+
- OpenCV
- Ultralytics YOLO
- NumPy
- Webcam

## Estrutura do Projeto

```
├── src/
│   └── webcam_detect_adaptive.py  # Script principal
├── runs-cube/                     # Modelos YOLO treinados
└── README.md                      # Este arquivo
```

O projeto foi simplificado para focar apenas nas funcionalidades essenciais de detecção e tracking de cubos mágicos.
