import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import messagebox, filedialog
from datetime import datetime, timedelta
import json
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm


# ========== Funções utilitárias ==========
def salvar_dados(plafond_mensal, orcamento_semanal, gastos):
    dados = {
        "plafond_mensal": plafond_mensal,
        "orcamento_semanal": orcamento_semanal,
        "gastos": [
            {"data": g["data"].strftime(
                "%d/%m/%Y"), "valor": g["valor"], "motivo": g["motivo"]}
            for g in gastos
        ],
    }
    with open("orcamento.json", "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)


def carregar_dados():
    try:
        with open("orcamento.json", "r", encoding="utf-8") as f:
            dados = json.load(f)
            gastos = [
                {
                    "data": datetime.strptime(g["data"], "%d/%m/%Y"),
                    "valor": g["valor"],
                    "motivo": g["motivo"],
                }
                for g in dados["gastos"]
            ]
            return dados["plafond_mensal"], dados["orcamento_semanal"], gastos
    except FileNotFoundError:
        return 0, 0, []


# ========== Classe Principal ==========
class GestorOrcamento(tb.Window):
    def __init__(self):
        super().__init__(title="Gestor de Orçamento Pessoal 💰", themename="cyborg")
        self.geometry("850x640")
        self.resizable(False, False)

        self.plafond_mensal, self.orcamento_semanal, self.gastos = carregar_dados()

        if self.plafond_mensal == 0 or self.orcamento_semanal == 0:
            self._criar_tela_inicial()
        else:
            self._criar_dashboard_ui()

    # ========== Tela Inicial ==========
    def _criar_tela_inicial(self):
        frame = tb.Frame(self, padding=30)
        frame.pack(expand=True)

        tb.Label(frame, text="Definir Orçamentos Iniciais",
                 font=("Segoe UI", 16, "bold")).pack(pady=15)

        tb.Label(frame, text="Plafond Mensal (Kz):").pack()
        self.entry_mensal = tb.Entry(frame, width=30)
        self.entry_mensal.pack(pady=5)

        tb.Label(frame, text="Orçamento Semanal (Kz):").pack()
        self.entry_semanal = tb.Entry(frame, width=30)
        self.entry_semanal.pack(pady=5)

        tb.Button(frame, text="Entrar no Dashboard", bootstyle="success",
                  command=self._salvar_iniciais).pack(pady=15)

    def _salvar_iniciais(self):
        try:
            self.plafond_mensal = float(self.entry_mensal.get())
            self.orcamento_semanal = float(self.entry_semanal.get())
        except ValueError:
            messagebox.showerror("Erro", "Insira valores numéricos válidos!")
            return

        salvar_dados(self.plafond_mensal, self.orcamento_semanal, [])
        for widget in self.winfo_children():
            widget.destroy()
        self._criar_dashboard_ui()

    # ========== Dashboard ==========
    def _criar_dashboard_ui(self):
        top = tb.Frame(self, padding=10)
        top.pack(fill="x")

        tb.Label(top, text="Gestor de Orçamento Pessoal 💰",
                 font=("Segoe UI", 18, "bold")).pack(side="left")

        self.label_plafond_mensal = tb.Label(
            top, text="", font=("Segoe UI", 10))
        self.label_plafond_mensal.pack(side="right", padx=20)

        # Área central
        center = tb.Frame(self, padding=15)
        center.pack(fill="both", expand=True)

        # Card principal (Plafond Semanal)
        self.label_semanal = tb.Label(
            center, text="", font=("Segoe UI", 28, "bold"))
        self.label_semanal.pack(pady=20)

        # Formulário de gastos
        form = tb.Labelframe(center, text="Registrar Gasto", padding=15)
        form.pack(pady=15, fill="x")

        tb.Label(form, text="Valor (Kz):").grid(
            row=0, column=0, sticky="w", padx=5)
        self.entry_valor = tb.Entry(form, width=15)
        self.entry_valor.grid(row=0, column=1, padx=5)

        tb.Label(form, text="Motivo:").grid(
            row=0, column=2, sticky="w", padx=5)
        self.entry_motivo = tb.Entry(form, width=30)
        self.entry_motivo.grid(row=0, column=3, padx=5)

        tb.Label(form, text="Data (dd/mm/aaaa):").grid(row=1,
                                                       column=0, sticky="w", padx=5)
        self.entry_data = tb.Entry(form, width=15)
        self.entry_data.grid(row=1, column=1, padx=5)
        self.entry_data.insert(0, datetime.now().strftime("%d/%m/%Y"))

        tb.Button(form, text="Adicionar", bootstyle="success", command=self.adicionar_gasto)\
            .grid(row=1, column=3, padx=5, pady=(8, 0), sticky="e")

        tb.Button(form, text="Adicionar Reposição", bootstyle="info-outline", command=self.abrir_reposicao)\
            .grid(row=2, column=1, columnspan=3, pady=(8, 0))

        # Botões de resumo
        btns = tb.Frame(center)
        btns.pack(pady=20)
        tb.Button(btns, text="Resumo Semanal", bootstyle="primary",
                  command=self.mostrar_resumo_semanal).grid(row=0, column=0, padx=10)
        tb.Button(btns, text="Gerar PDF Mensal", bootstyle="warning",
                  command=self.exportar_pdf).grid(row=0, column=1, padx=10)

        # Lista de gastos/ganhos
        self.lista = tk.Listbox(center, height=10, width=90)
        self.lista.pack(pady=10)

        # Botão de eliminar
        tb.Button(center, text="🗑️ Eliminar Selecionado",
                  bootstyle="danger-outline", command=self.eliminar_item).pack(pady=0)

        self.atualizar_tudo()

    # ========== Funções principais ==========
    def adicionar_gasto(self):
        try:
            valor = float(self.entry_valor.get())
            motivo = self.entry_motivo.get().strip()
            data = datetime.strptime(self.entry_data.get().strip(), "%d/%m/%Y")
        except ValueError:
            messagebox.showerror("Erro", "Insere valores válidos.")
            return

        self.gastos.append({"data": data, "valor": valor, "motivo": motivo})
        salvar_dados(self.plafond_mensal, self.orcamento_semanal, self.gastos)
        self.entry_valor.delete(0, "end")
        self.entry_motivo.delete(0, "end")
        self.atualizar_tudo()

    def abrir_reposicao(self):
        popup = tb.Toplevel(self)
        popup.title("Adicionar Reposição / Ganho")
        popup.geometry("380x240")
        popup.resizable(False, False)

        frm = tb.Frame(popup, padding=12)
        frm.pack(fill="both", expand=True)

        tb.Label(frm, text="Valor (Kz):").grid(
            row=0, column=0, sticky="w", padx=6, pady=8)
        entry_valor = tb.Entry(frm, width=18)
        entry_valor.grid(row=0, column=1, padx=6, pady=8)

        tb.Label(frm, text="Descrição:").grid(
            row=1, column=0, sticky="w", padx=6, pady=8)
        entry_desc = tb.Entry(frm, width=26)
        entry_desc.grid(row=1, column=1, padx=6, pady=8)
        entry_desc.insert(0, "Reposição semanal")

        tb.Label(frm, text="Data (dd/mm/aaaa):").grid(row=2,
                                                      column=0, sticky="w", padx=6, pady=8)
        entry_data = tb.Entry(frm, width=14)
        entry_data.grid(row=2, column=1, padx=6, pady=8)
        entry_data.insert(0, datetime.now().strftime("%d/%m/%Y"))

        def confirmar():
            try:
                valor = float(entry_valor.get())
                data = datetime.strptime(entry_data.get().strip(), "%d/%m/%Y")
                desc = entry_desc.get().strip()
                if valor <= 0:
                    raise ValueError
            except Exception:
                messagebox.showerror(
                    "Erro", "Insere valores válidos (data e número positivo).")
                return

            self.gastos.append({
                "data": data,
                "valor": -valor,
                "motivo": f"💰 [Ganho] {desc}"
            })
            salvar_dados(self.plafond_mensal,
                         self.orcamento_semanal, self.gastos)
            popup.destroy()
            self.atualizar_tudo()

        tb.Button(frm, text="Confirmar", bootstyle="success", command=confirmar).grid(
            row=3, column=0, columnspan=2, pady=14)

    def eliminar_item(self):
        selecao = self.lista.curselection()
        if not selecao:
            messagebox.showwarning(
                "Aviso", "Seleciona um item da lista primeiro.")
            return

        indice = selecao[0]
        gasto_selecionado = sorted(
            self.gastos, key=lambda x: x["data"], reverse=True)[indice]

        confirmar = messagebox.askyesno(
            "Confirmar", f"Tens certeza que queres eliminar este item?\n\n{gasto_selecionado['motivo']} — {abs(gasto_selecionado['valor']):,.2f} Kz")
        if confirmar:
            self.gastos.remove(gasto_selecionado)
            salvar_dados(self.plafond_mensal,
                         self.orcamento_semanal, self.gastos)
            self.atualizar_tudo()
            messagebox.showinfo(
                "Eliminado", "O item foi removido com sucesso.")

    def atualizar_tudo(self):
        hoje = datetime.now()
        total_mensal_gastos = sum(abs(
            g["valor"]) for g in self.gastos if g["valor"] > 0 and g["data"].month == hoje.month)
        total_mensal_ganhos = sum(abs(
            g["valor"]) for g in self.gastos if g["valor"] < 0 and g["data"].month == hoje.month)
        limite_semanal_inicio = hoje - timedelta(days=7)
        total_semanal_gastos = sum(abs(
            g["valor"]) for g in self.gastos if g["valor"] > 0 and g["data"] >= limite_semanal_inicio)
        total_semanal_ganhos = sum(abs(
            g["valor"]) for g in self.gastos if g["valor"] < 0 and g["data"] >= limite_semanal_inicio)

        restante_mensal = max(self.plafond_mensal +
                              total_mensal_ganhos - total_mensal_gastos, 0.0)
        restante_semanal = max(self.orcamento_semanal +
                               total_semanal_ganhos - total_semanal_gastos, 0.0)

        self.label_plafond_mensal.config(
            text=f"Plafond mensal restante: {restante_mensal:,.2f} Kz")
        self.label_semanal.config(
            text=f"Plafond semanal: {restante_semanal:,.2f} Kz")

        self.lista.delete(0, "end")
        for g in sorted(self.gastos, key=lambda x: x["data"], reverse=True):
            tipo = "Despesa" if g["valor"] > 0 else "Ganho"
            self.lista.insert(
                "end", f"{g['data'].strftime('%d/%m/%Y')} - {g['motivo']} ({tipo}) — {abs(g['valor']):,.2f} Kz")

    def mostrar_resumo_semanal(self):
        hoje = datetime.now()
        inicio_semana = hoje - timedelta(days=7)
        gastos_semana = [g for g in self.gastos if g["data"] >= inicio_semana]
        total = sum(abs(g["valor"]) if g["valor"] > 0 else -
                    abs(g["valor"]) for g in gastos_semana)
        messagebox.showinfo(
            "Resumo Semanal", f"Total líquido na semana: {total:,.2f} Kz")

    def exportar_pdf(self):
        caminho = filedialog.asksaveasfilename(
            defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
        if not caminho:
            return

        c = canvas.Canvas(caminho, pagesize=A4)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(2 * cm, 27 * cm, "Resumo Mensal - Gestor de Orçamento")
        c.setFont("Helvetica", 12)
        y = 25 * cm

        for g in sorted(self.gastos, key=lambda x: x["data"]):
            linha = f"{g['data'].strftime('%d/%m/%Y')} - {g['motivo']} — {abs(g['valor']):,.2f} Kz"
            c.drawString(2 * cm, y, linha)
            y -= 0.6 * cm
            if y < 2 * cm:
                c.showPage()
                y = 27 * cm
        c.save()
        messagebox.showinfo("Sucesso", f"PDF salvo em:\n{caminho}")


# ========== Execução ==========
if __name__ == "__main__":
    app = GestorOrcamento()
    app.mainloop()
