import os
from operator import index
from tkinter import filedialog, messagebox, Canvas, Toplevel, Scrollbar, Button
import numpy as np
import ttkbootstrap as ttk
from PIL import Image, ImageDraw, ImageTk
from ttkbootstrap.constants import *

def bound_box_image(input_image):
    img = Image.open(input_image).convert("RGBA")
    bbox = img.getbbox()
    img_cortada = img.crop(bbox)

    return img_cortada

def processar_imagem(input_image, gap_linha, gap_entre_caracteres, check_fancycounter):
    img = bound_box_image(input_image)
    img_array = np.array(img)

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
    caracteres_com_fancycounter = 10
    caracteres_a_comparar = caracteres[:caracteres_com_fancycounter]  # Apenas os 10 primeiros

    # Encontrar o maior caractere entre os 10 primeiros
    if caracteres_a_comparar:
        maior_caractere = max(caracteres_a_comparar, key=lambda x: x[1] - x[0])
        maior_largura = (maior_caractere[1] - maior_caractere[0]) + 2 * gap_linha

    imagens_caracteres = []

    index = 0
    for inicio_caractere, fim_caractere in caracteres:
        caracteres_com_fancycounter = 10
        largura_caractere = fim_caractere - inicio_caractere

        nova_largura = largura_caractere
        turn_on_fancycounter = presset_fancycounter(check_fancycounter)

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

def presset_fancycounter(check_fancycounter):
    return check_fancycounter.get()

def salvar_arquivos_em_lote(imagens_processadas, caminhos_saidas):
    for img, caminho in zip(imagens_processadas, caminhos_saidas):
        try:
            img.save(caminho)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar a imagem {caminho}: {e}")

def previsualizar_multiplos_arquivos(entrada, gap_linha, gap_entre, saida,check_fancycounter):
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
        abrir_previsualizacao(imagens_processadas[0], lambda: salvar_arquivos_em_lote(imagens_processadas, caminhos_saida))

    except Exception as e:
        messagebox.showerror("Erro", f"Erro na pré-visualização: {e}")

def abrir_previsualizacao(imagem_final, salvar_func=None):
    previsualizacao = Toplevel()
    previsualizacao.title("Pré-visualização")
    previsualizacao.geometry("800x500")

    canvas = Canvas(previsualizacao, bg="white")
    h_scroll = Scrollbar(previsualizacao, orient=HORIZONTAL, command=canvas.xview)
    canvas.config(xscrollcommand=h_scroll.set)

    img_tk = ImageTk.PhotoImage(imagem_final)
    canvas.image = img_tk
    canvas.create_image(0, 0, anchor="nw", image=img_tk)
    canvas.config(scrollregion=canvas.bbox("all"))

    canvas.pack(side="top", fill="both", expand=True)
    h_scroll.pack(side="bottom", fill="x")

    confirm_button = Button(previsualizacao, text="Salvar", command=lambda: [salvar_func(), previsualizacao.destroy()])
    confirm_button.pack(side="right", padx=10, pady=10)

    Button(previsualizacao, text="Cancelar", command=previsualizacao.destroy).pack(side="left", padx=10, pady=10)

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
    ttk.Button(root, text="Pré-visualizar", command=lambda: previsualizar_multiplos_arquivos(entrada_arquivos, gap_linha, gap_entre, entrada_pasta,check_fancycounter)).pack(anchor="w", padx=10, pady=20)

    root.mainloop()

if __name__ == "__main__":
    criar_interface()