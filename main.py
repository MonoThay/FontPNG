import os
from tkinter import filedialog, messagebox, Canvas, Toplevel, Scrollbar, Button, Label
import numpy as np
import ttkbootstrap as ttk
from PIL import Image, ImageDraw, ImageTk

def bound_box_image(input_image):
    img = Image.open(input_image).convert("RGBA")
    bbox = img.getbbox()
    img_cortada = img.crop(bbox)

    return img_cortada

def processar_imagem(input_image, gap_linha, gap_entre_caracteres, check_fancycounter):
    img = bound_box_image(input_image)
    img_array = np.array(img)

    caracteres_com_fancycounter = 10

    # Identificar colunas não transparentes
    non_transparent_cols = np.any(img_array[:, :, 3] > 0, axis=0)

    caracteres = []
    inicio = None

    # Detectar os intervalos de cada caractere
    for i, col in enumerate(non_transparent_cols):
        if col and inicio is None:
            inicio = i
        elif not col and inicio is not None:
            fim = i
            caracteres.append((inicio, fim))
            inicio = None

    if inicio is not None:
        caracteres.append((inicio, len(non_transparent_cols)))

    # Limitar a análise aos primeiros 10 caracteres
    caracteres_a_comparar = caracteres[:caracteres_com_fancycounter]

    # Encontrar o maior caractere entre os 10 primeiros
    if caracteres_a_comparar:
        maior_caractere = max(caracteres_a_comparar, key=lambda x: x[1] - x[0])
        maior_largura = (maior_caractere[1] - maior_caractere[0]) + 2 * gap_linha

    imagens_caracteres = []

    index = 0
    for inicio_caractere, fim_caractere in caracteres:
        largura_caractere = fim_caractere - inicio_caractere

        nova_largura = largura_caractere
        turn_on_fancycounter = switch_fancy_counter(check_fancycounter)

        if index < caracteres_com_fancycounter and turn_on_fancycounter == 1:
            nova_largura = maior_largura

        # Recortar o caractere
        caractere_crop = img.crop((inicio_caractere, 0, fim_caractere, img.height))

        nova_altura = img.height + 1

        # Criar uma nova imagem para o caractere alinhado
        caractere_img = Image.new("RGBA", (nova_largura, nova_altura + gap_linha), (0, 0, 0, 0))

        # Centralizar o caractere horizontalmente
        inicio_centro = (nova_largura - largura_caractere) // 2
        caractere_img.paste(caractere_crop, (inicio_centro, 0))

        # Desenhar uma linha contínua preta abaixo do caractere

        if turn_on_fancycounter == 1:
            if index < caracteres_com_fancycounter:
                draw = ImageDraw.Draw(caractere_img)
                linha_posicao_y = nova_altura
                draw.line(
                    [0, linha_posicao_y, nova_largura, linha_posicao_y],
                    fill=(0, 0, 0, int(0.02 * 255)),  # Preto com 2% de opacidade
                    width=1
                )

        index += 1

        imagens_caracteres.append(caractere_img)

    #Cria iamgem final
    largura_total = sum(img.width for img in imagens_caracteres) + gap_entre_caracteres * (len(imagens_caracteres) - 1)
    altura_maxima = max(img.height for img in imagens_caracteres)

    imagem_final = Image.new("RGBA", (largura_total, altura_maxima), (0, 0, 0, 0))
    x_offset = 0
    for img in imagens_caracteres:
        imagem_final.paste(img, (x_offset, 0))
        x_offset += img.width + gap_entre_caracteres

    return imagem_final

def selecionar_arquivos_entrada(entry):
    arquivos = filedialog.askopenfilenames(filetypes=[("Imagens", "*.png;*.jpg;*.jpeg")])
    if arquivos:
        entry.delete(0, "end")
        entry.insert(0, ";".join(arquivos))  # Salva a lista de arquivos separada por ponto e vírgula.

def selecionar_pasta_saida(entry):
    pasta = filedialog.askdirectory()
    if pasta:
        entry.delete(0, "end")
        entry.insert(0, pasta)

def switch_fancy_counter(check_fancycounter):
    return check_fancycounter.get()

def verificar_tamanho_da_imagem(img, caminho):
    TAMANHO_MAXIMO_KB = 1228800  # 1200 KB (informar em bytes)
    DIMENSAO_MAXIMA = 16000  # 16 mil pixels (largura ou altura)

    # Verificar tamanho do arquivo
    tamanho_imagem_kb = os.path.getsize(caminho)
    if tamanho_imagem_kb > TAMANHO_MAXIMO_KB:
        messagebox.showerror("Erro", f"A imagem {caminho} é maior que o limite de 1.200 KB ({tamanho_imagem_kb:.2f} KB).")
        return False

    # Verificar dimensões da imagem
    largura, altura = img.size
    if altura > DIMENSAO_MAXIMA or largura > DIMENSAO_MAXIMA:
        messagebox.showerror("Erro",f"A imagem {caminho} tem dimensões maiores que o limite de 16000 pixels ({largura}x{altura} pixels).")
        return False
    return True

def salvar_arquivos_em_lote(imagens_processadas, caminhos_saidas,check_criar_nova_pasta):
    check_switch = check_criar_nova_pasta.get()
    check_imagem_salva = True

    if check_switch == 0:
        for img, caminho in zip(imagens_processadas, caminhos_saidas):
            try:
                if verificar_tamanho_da_imagem(img, caminho):  # Verifica se a imagem é válida antes de salvar
                    img.save(caminho)
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar a imagem {caminho}: {e}")
                check_imagem_salva = False
    elif check_switch == 1:
        for img, caminho in zip(imagens_processadas, caminhos_saidas):
            try:
                if verificar_tamanho_da_imagem(img, caminho):  # Verifica se a imagem é válida antes de salvar
                    pasta_nova = os.path.join(os.path.dirname(caminho), "FontPNG-export")
                    if not os.path.exists(pasta_nova):
                        os.makedirs(pasta_nova)
                    novo_caminho = os.path.join(pasta_nova, os.path.basename(caminho))
                    img.save(novo_caminho)

            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar a imagem {caminho}: {e}")
                check_imagem_salva = False
    else:
        messagebox.showerror("Erro", f"Erro ao salvar a imagem {caminho}: {e}")
        check_imagem_salva = False

    # Confirmação que a imagem foi salva
    if check_imagem_salva == True:
        messagebox.showinfo("Salvar", f"Arquivos salvos com sucesso!")

def previsualizar_multiplos_arquivos(entrada, gap_linha, gap_entre, saida,check_fancycounter, check_criar_nova_pasta):
    try:
        gap_linha = int(gap_linha.get())
        gap_entre = int(gap_entre.get())
        input_images = entrada.get().split(";")  # Divide a lista de arquivos.
        output_path = saida.get()

        if not input_images or any(not os.path.isfile(img) for img in input_images):
            raise FileNotFoundError("Um ou mais arquivos de entrada não foram encontrados.")
        if gap_linha < 0 or gap_entre < 0:
            raise ValueError("Os valores de gap devem ser números positivos.")
        if not output_path:
            raise ValueError("Por favor, selecione uma pasta de saída.")

        imagens_processadas = []
        caminhos_saida = []
        for i, img_path in enumerate(input_images):
            imagem_final = processar_imagem(img_path, gap_linha, gap_entre,check_fancycounter)
            imagens_processadas.append(imagem_final)

            nome_base = os.path.basename(img_path)
            caminho_saida = os.path.join(output_path, f"{nome_base}")
            caminhos_saida.append(caminho_saida)

        # Pré-visualização de apenas o primeiro arquivo para simplificação
        abrir_previsualizacao(imagens_processadas[0], lambda: salvar_arquivos_em_lote(imagens_processadas, caminhos_saida,check_criar_nova_pasta))

    except Exception as e:
        messagebox.showerror("Erro", f"Erro na pré-visualização: {e}")

def abrir_previsualizacao(imagem_final, salvar_func=None):
    previsualizacao = Toplevel()
    previsualizacao.title("Pré-visualização")
    previsualizacao.geometry("800x600")

    # Configuração do grid
    previsualizacao.grid_rowconfigure(0, weight=1)
    previsualizacao.grid_columnconfigure(0, weight=1)

    # Canvas e barras de rolagem
    canvas = Canvas(previsualizacao, bg="white")
    h_scroll = Scrollbar(previsualizacao, orient="horizontal", command=canvas.xview)
    v_scroll = Scrollbar(previsualizacao, orient="vertical", command=canvas.yview)

    canvas.config(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)

    # Carregar a imagem original
    img_original = imagem_final  # A imagem PIL original
    img_tk = ImageTk.PhotoImage(img_original)
    canvas.image_id = canvas.create_image(0, 0, anchor="nw", image=img_tk)
    canvas.config(scrollregion=canvas.bbox("all"))

    # Estado do zoom
    zoom_state = {"current_zoom": 100}

    # Função para aplicar zoom com base no valor do slider
    def aplicar_zoom(val):
        new_zoom = float(val)
        zoom_percent = new_zoom / 100
        new_width = int(img_original.width * zoom_percent)
        new_height = int(img_original.height * zoom_percent)

        # Redimensionar a imagem
        img_resized = img_original.resize((new_width, new_height), Image.Resampling.LANCZOS)
        img_tk_resized = ImageTk.PhotoImage(img_resized)

        # Atualizar a imagem no canvas
        canvas.image = img_tk_resized
        canvas.itemconfig(canvas.image_id, image=img_tk_resized)
        canvas.config(scrollregion=canvas.bbox("all"))

        zoom_state["current_zoom"] = new_zoom

    # Posicionamento no grid
    canvas.grid(row=0, column=0, sticky="nsew")
    h_scroll.grid(row=1, column=0, sticky="ew")
    v_scroll.grid(row=0, column=1, sticky="ns")

    # Slider para controle de zoom
    zoom_label = ttk.Label(previsualizacao, text="Zoom")
    zoom_label.grid(row=2, column=0, sticky="n", padx=10, pady=5)

    zoom_slider = ttk.Scale(previsualizacao, from_=1, to=200, orient="horizontal", command=aplicar_zoom)
    zoom_slider.set(100)  # Começa com zoom de 100%
    zoom_slider.grid(row=3, column=0, sticky="ew", padx=100, pady=5)

    # Botões de salvar e cancelar
    confirm_button = Button(previsualizacao, text="Salvar", command=lambda: [salvar_func(), previsualizacao.destroy()])
    confirm_button.grid(row=3, column=0, sticky="e", padx=10, pady=10)

    cancel_button = Button(previsualizacao, text="Cancelar", command=previsualizacao.destroy)
    cancel_button.grid(row=3, column=0, sticky="w", padx=10, pady=10)

def help():
    help_window = Toplevel()
    help_window.title("Ajuda - FontPNG")

    # Criando a área de texto para exibir o conteúdo de ajuda
    help_text = """
    TEXTO DO CHAT GPT VAI SER ATUALIZADO
    
    ### Ajuda - FontPNG

    Este programa permite processar imagens de texto em formato PNG, JPG ou JPEG, realizando o recorte dos caracteres em cada imagem e ajustando seu formato e espaçamento. Além disso, você pode escolher a opção de criar uma nova pasta para salvar as imagens processadas.

    #### Passos para usar:

    1. **Seleção de Arquivos de Entrada**:
       - Clique no botão **"Selecionar Arquivos"** para escolher uma ou mais imagens de texto para processamento.
       - As imagens devem estar em formatos compatíveis (PNG, JPG ou JPEG).

    2. **Seleção de Pasta de Saída**:
       - Clique no botão **"Selecionar Pasta"** para escolher onde as imagens processadas serão salvas.
       - O programa permite que você salve as imagens na pasta atual ou crie uma nova pasta.

    3. **Configuração dos Parâmetros**:
       - **Gap Fancycounter (px)**: Defina o espaçamento extra em pixels para o efeito "fancycounter" nas imagens.
       - **Gap entre Caracteres (px)**: Ajuste o espaçamento entre os caracteres recortados.
       - **Habilitar Fancycounter**: Se ativado, o programa ajustará a largura dos caracteres recortados para um tamanho padrão.

    4. **Pré-visualização**:
       - Clique em **"Pré-visualizar"** para ver a imagem processada antes de salvar. A pré-visualização pode ser ajustada com zoom para visualizar melhor os detalhes da imagem.

    5. **Opção de Criar Nova Pasta**:
       - Se ativado, o programa criará uma nova pasta chamada "FontPNG-export" para salvar as imagens processadas. Caso contrário, as imagens serão salvas diretamente na pasta de destino escolhida.

    6. **Salvar Imagens**:
       - Após a pré-visualização, você pode salvar as imagens processadas clicando em **"Salvar"** ou cancelar a operação.

    #### Funções adicionais:

    - **Zoom na pré-visualização**: Ajuste o zoom da imagem pré-visualizada com o controle deslizante para um maior ou menor nível de detalhe.

    - **Erros**: Caso ocorra algum erro durante a execução, uma mensagem será exibida informando o problema. Verifique se os arquivos de entrada estão corretos e se a pasta de saída foi selecionada adequadamente.

    #### Dúvidas e Suporte:
    Se você tiver algum problema ao usar o programa, por favor, verifique se todas as etapas foram seguidas corretamente. Caso o erro persista, entre em contato com o desenvolvedor para obter mais assistência.
    """

    # Criando um widget de label para mostrar o texto de ajuda
    help_label = Label(help_window, text=help_text, justify="left", font=("Arial", 10), padx=10, pady=10)
    help_label.pack(expand=True, fill="both")

    # Botão para fechar a janela de ajuda
    close_button = Button(help_window, text="Fechar", command=help_window.destroy)
    close_button.pack(pady=10)

def criar_interface():
    root = ttk.Window("FontPNG")
    style = ttk.Style("flatly")
    root.iconbitmap("icon.ico")

    # Widgets para selecionar arquivos de entrada
    ttk.Label(root, text="Arquivos de entrada:").pack(anchor="w", padx=10, pady=(10, 0))
    entrada_arquivos = ttk.Entry(root, width=50)
    entrada_arquivos.pack(anchor="w",padx=10, pady=5)
    ttk.Button(root, text="Selecionar Arquivos", command=lambda: selecionar_arquivos_entrada(entrada_arquivos)).pack(anchor="w", padx=10, pady=5)

    # Widgets para selecionar pasta de saída
    ttk.Label(root, text="Pasta de saída:").pack(anchor="w", padx=10, pady=(10, 0))
    entrada_pasta = ttk.Entry(root, width=50)
    entrada_pasta.pack(anchor="w", padx=10, pady=5)
    ttk.Button(root, text="Selecionar Pasta", command=lambda: selecionar_pasta_saida(entrada_pasta)).pack(anchor="w", padx=10, pady=5)

    #toggle criar pasta de saida
    check_criar_nova_pasta = ttk.IntVar()
    ttk.Checkbutton(root, bootstyle="round-toggle", text="Criar nova pasta", variable=check_criar_nova_pasta, onvalue=1, offvalue=0 ).pack(anchor="w", padx=10, pady=5)

    # Gaps
    ttk.Label(root, text="Gap fancycounter (px):").pack(anchor="w", padx=10, pady=(10, 0))
    gap_linha = ttk.Entry(root, width=10)
    gap_linha.insert(0, "1")
    gap_linha.pack(anchor="w", padx=10, pady=5)

    ttk.Label(root, text="Gap entre caracteres (px):").pack(anchor="w", padx=10, pady=(10, 0))
    gap_entre = ttk.Entry(root, width=10)
    gap_entre.insert(0, "1")
    gap_entre.pack(anchor="w", padx=10, pady=5)

    #botão controle fancycounter (retorna 0 e 1)
    check_fancycounter = ttk.IntVar()
    ttk.Checkbutton(root, bootstyle="round-toggle", text="Habilitar Fancycounter", variable= check_fancycounter, onvalue=1, offvalue=0).pack(anchor="w", padx=10, pady=15)

    # Botão para pré-visualizar
    ttk.Button(root, text="Pré-visualizar", command=lambda: previsualizar_multiplos_arquivos(entrada_arquivos, gap_linha, gap_entre, entrada_pasta,check_fancycounter,check_criar_nova_pasta)).pack(anchor="w", padx=10, pady=20)
    #ttk.Button(root, text="Help", command=help).pack(anchor="w", padx=10, pady=10)

    root.mainloop()

if __name__ == "__main__":
    criar_interface()