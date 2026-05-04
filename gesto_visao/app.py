# ■ app.py — PARTE 1/3: Imports, Configuração UDP e MediaPipe
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
# MÓDULO DE VISÃO — Reconhecimento de Gestos com MediaPipe
# ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■

# ■■ BLOCO 1: IMPORTAÇÕES ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
import cv2             # OpenCV: abre a câmera e desenha na tela
import mediapipe as mp # MediaPipe: detecta a mão e os dedos
import socket          # socket: permite enviar dados pela rede (UDP)
import time            # time: controla o intervalo entre envios

# ■■ BLOCO 2: CONFIGURAÇÃO DO UDP ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
# AF_INET = protocolo IPv4 | SOCK_DGRAM = UDP (sem confirmação)
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
JAVA_HOST = '127.0.0.1'  # '127.0.0.1' = este mesmo computador
JAVA_PORT = 5000         # porta onde o Java está escutando
ultimo_envio = 0
INTERVALO_ENVIO = 1.5    # no máximo 1 comando a cada 1.5 segundos

# ■■ BLOCO 3: INICIALIZAÇÃO DO MEDIAPIPE ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils # Desenha os pontos na tela

# max_num_hands=1 → detecta só 1 mão | min_detection_confidence=0.7
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

# ■ app.py — PARTE 2/3: Funções de Detecção de Gesto
# ■■ BLOCO 4: FUNÇÃO QUE ANALISA O GESTO ■■■■■■■■■■■■■■■■■■■■■■■■■■■■
def detectar_gesto(landmarks):
    '''Recebe 21 landmarks. Retorna MAO_ABERTA, MAO_FECHADA ou DESCONHECIDO.'''
    TIPS = [8, 12, 16, 20] # pontas: indicador, médio, anelar, mindinho
    PIPS = [6, 10, 14, 18] # meio: indicador, médio, anelar, mindinho
    dedos_abertos = 0
    
    # y cresce para BAIXO na imagem! TIP.y < PIP.y = dedo ereto
    for tip_id, pip_id in zip(TIPS, PIPS):
        if landmarks[tip_id].y < landmarks[pip_id].y:
            dedos_abertos += 1
            
    if dedos_abertos >= 4:
        return 'MAO_ABERTA'   # 4+ dedos levantados
    elif dedos_abertos == 0:
        return 'MAO_FECHADA'  # punho fechado
    else:
        return 'DESCONHECIDO' # estado intermediário

# ■■ BLOCO 5: MAPEIA GESTO PARA COMANDO UDP ■■■■■■■■■■■■■■■■■■■■■■■■■
def gesto_para_comando(gesto):
    '''Converte o nome do gesto em um comando que o Java entende.'''
    mapa = {
        'MAO_ABERTA': 'PLAY_PAUSE', # Mão aberta → pausar/tocar YouTube
        'MAO_FECHADA': 'LIGAR_LUZ', # Mão fechada → chamar API REST
    }
    return mapa.get(gesto, None) # None se gesto desconhecido


# ■ app.py — PARTE 3/3: Loop Principal e Envio UDP
# ■■ BLOCO 6: FUNÇÃO PRINCIPAL ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
def main():
    global ultimo_envio
    cap = cv2.VideoCapture(0) # 0 = câmera padrão do computador
    
    if not cap.isOpened():
        print('ERRO: Não foi possível abrir a câmera!')
        return
        
    print('Câmera aberta! Mostre sua mão. Pressione Q para sair.')
    
    while True:
        ret, frame = cap.read() # captura 1 frame da câmera
        if not ret: 
            break
            
        frame = cv2.flip(frame, 1) # espelha (como um espelho)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        resultado = hands.process(rgb_frame) # MediaPipe analisa
        
        gesto_atual = 'NENHUMA MAO'
        comando_atual = None
        
        if resultado.multi_hand_landmarks:
            for hand_landmarks in resultado.multi_hand_landmarks:
                mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS) # desenha pontos
                
                gesto_atual = detectar_gesto(hand_landmarks.landmark)
                comando_atual = gesto_para_comando(gesto_atual)
                
                # ■■ ENVIO UDP ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
                agora = time.time()
                if comando_atual and (agora - ultimo_envio) > INTERVALO_ENVIO:
                    mensagem = comando_atual.encode('utf-8') # texto → bytes
                    udp_socket.sendto(mensagem, (JAVA_HOST, JAVA_PORT))
                    print(f'Gesto: {gesto_atual} -> Enviado: {comando_atual}')
                    ultimo_envio = agora
                    
        # ■■ INTERFACE VISUAL ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
        cor = (0,255,0) if gesto_atual != 'NENHUMA MAO' else (0,0,255)
        cv2.putText(frame, f'Gesto: {gesto_atual}', (10,40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, cor, 2)
        
        if comando_atual:
            cv2.putText(frame, f'Cmd: {comando_atual}', (10,80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,200,0), 2)
            
        cv2.imshow('Reconhecimento de Gestos', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'): 
            break # Q para sair
            
    cap.release()
    cv2.destroyAllWindows()
    udp_socket.close()

# ■■ BLOCO 7: PONTO DE ENTRADA ■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■
if __name__ == '__main__':
    main()