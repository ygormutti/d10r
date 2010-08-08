#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
Módulo de interface gráfica

Copyright (C) 2010  Ygor Mutti
Licenciado sob GPLv3, com texto disponível no arquivo COPYING
'''

import time
import threading
import Tkinter as tk

from utils import formatah, plataforma, WINDOWS


ICON = 'icons/d10r.ico' if plataforma() == WINDOWS else '@icons/d10r.xbm'


# FIXME: Como easygui utiliza ICON e gui utiliza easygui é preciso importar
# depois da definição de ICON
import easygui as eg


TITLE = 'd10r'


class FimAlcancado(Exception):
    pass


class Cronometro(threading.Thread):
    '''Cronômetro assíncrono com threads.'''
    def __init__(self, fim=None, h=False):
        super(Cronometro, self).__init__()
        if fim and h:
            self.fim = fim * 3600
        else:
            self.fim = fim
        self._decorrido = 0
        self._pausado = False
        self._parado = False

    def run(self):
        while True:
            if self.fim != None and self.decorrido >= self.fim:
                self._decorrido = self.fim
                self.parar()
            if self._parado:
                break
            time.sleep(1)
            if not self._pausado:
                self._decorrido += 1

    def pausar(self):
        '''Pausa o cronômetro ou continua a contar, se estiver pausado.'''
        if self._pausado:
            self._pausado = False
        else:
            self._pausado = True

    def parar(self):
        '''Encerra a contagem e finaliza a thread.'''
        self._parado = True

    @property
    def decorrido(self):
        '''Tempo em segundos decorrido desde o início da contagem.'''
        return self._decorrido

    @property
    def decorridoh(self):
        '''Mesmo que decorrido, porém retorna o valor em horas.'''
        return self._decorrido / 3600.0

    @property
    def isparado(self):
        return self._parado


def root_config(delete, title=TITLE, iconname=TITLE, icon=ICON):
    '''root_config(delete, title=TITLE, iconname=TITLE, icon=ICON) -> Tkinter.Tk
    delete -> method
    title -> str
    icon -> str
    iconname -> str

    Configura o widget raiz. 'delete' é o método executado ao fechar a janela,
    'title' é o título da janela; 'icon' é o caminh para o ícone que aparece no
    canto da janela e 'iconname' é o nome que aparece na barra de tarefas.'''
    root = tk.Tk()
    root.title(title)
    root.protocol(delete)
    root.iconname(iconname)
    root.wm_iconbitmap(ICON)
    return root


class CronometroDialog:
    '''Janela que exibe o nome de uma atividade, o tempo decorrido, o saldo e
    botões para que o usuário pause ou pare o cronômetro.'''

    def __init__(self, atividade, parar=True):
        self.atividade = atividade
        if parar:
            self.cronometro = Cronometro(atividade.saldo, True)
        else:
            self.cronometro = Cronometro(None)
        self.construir()
        self.start()
        self.root.mainloop()

    def start(self):
        if not self.cronometro.isAlive():
            self.cronometro.start()
        self._refresh()

    def _refresh(self):
        self.tempoDecorridoLbl.config(text=formatah(-self.cronometro.decorridoh,
                                      segundos=True))
        if not self.cronometro.isparado:
            self.tempoDecorridoLbl.after(200, self._refresh)
        else:
            self.fechar()

    def fechar(self):
        self.root.quit()
        self.root.destroy()

    def pararCb(self):
        self.cronometro.parar()
        self.fechar()

    def pausarCb(self):
        self.cronometro.pausar()

    def construir(self):
        '''Cria a janela com os widgets e configura o label para ser atualizado
        com o tempo decorrido.'''
        ### Janela ###
        self.root = root_config(self.pararCb,
                                u'%s - Atividade: %s' % (TITLE,
                                                         self.atividade.nome))
        self.root.wm_attributes('-topmost', 1)

        ### Frames ###

        mainFrame = tk.Frame(self.root)
        mainFrame.pack()

        ### Labels ###

        atividadeLabel = tk.Label(mainFrame, text='Decorrido/Saldo: ', justify='left')
        atividadeLabel.pack(side='left', expand=True)

        self.tempoDecorridoLbl = tk.Label(mainFrame,
                                 text=formatah(-self.cronometro.decorridoh, True))
        self.tempoDecorridoLbl.pack(side='left', expand=True)

        tempoSaldoLbl = tk.Label(mainFrame,
                                 text='/ ' + formatah(self.atividade.saldo))
        tempoSaldoLbl.pack(side='left', expand=True)

        ### Buttons ###
        pausarBtn = tk.Checkbutton(mainFrame, text='Pausar', command=self.pausarCb)
        pausarBtn.pack(side='left')

        pararBtn = tk.Button(mainFrame, text='Finalizar', command=self.pararCb)
        pararBtn.pack(side='left')


class HoraSpinDialog:
    '''Diálogo com 3 Spinbox que permitem ao usuário especificar uma quantidade
    de horas, minutos e segundos.'''
    def __init__(self, msg):
        self.msg = msg
        self.construir()
        self.root.mainloop()

    def get(self):
        try:
            return (self.horas, self.minutos, self.segundos)
        except AttributeError:
            return None

    def construir(self):
        self.root = root_config(self.fechar, '%s - Debitar' % TITLE)

        msglbl = tk.Label(self.root, text=self.msg)
        msglbl.pack()

        formframe = tk.Frame(self.root)
        formframe.pack()

        lblsframe = tk.Frame(formframe)
        lblsframe.pack(side='left')

        spinsframe = tk.Frame(formframe)
        spinsframe.pack(side='left')

        horalbl = tk.Label(lblsframe, text='Horas: ')
        horalbl.pack()

        minutolbl = tk.Label(lblsframe, text='Minutos: ')
        minutolbl.pack()

        segundolbl = tk.Label(lblsframe, text='Segundos: ')
        segundolbl.pack()

        self._horaspn = tk.Spinbox(spinsframe, values=range(100))
        self._horaspn.pack()

        self._minutospn = tk.Spinbox(spinsframe, values=range(100))
        self._minutospn.pack()

        self._segundospn = tk.Spinbox(spinsframe, values=range(100))
        self._segundospn.pack()

        dialogobtnframe = tk.Frame(self.root)
        dialogobtnframe.pack(anchor=tk.E)

        cancelarbtn = tk.Button(dialogobtnframe, command=self.fechar,
                                text='Cancelar')
        cancelarbtn.pack(side=tk.LEFT)

        okbtn = tk.Button(dialogobtnframe, text='OK', command=self.okbtn_cb)
        okbtn.pack(side=tk.LEFT)

    def okbtn_cb(self):
        self.horas = int(self._horaspn.get())
        self.minutos = int(self._minutospn.get())
        self.segundos = int(self._segundospn.get())
        self.fechar()

    def fechar(self):
        self.root.quit()
        self.root.destroy()


class PrioridadeDialog:
    '''Janela que exibe uma lista com atividades e botões para que o usuário
    possa ordená-las por ordem descrescente de prioridade.'''

    def __init__(self, atividades):
        '''atividades -> list

        'atividades' é uma lista contendo os nomes das atividades.'''
        self.construir(atividades)
        self.root.mainloop()

    def get(self):
        try:
            return self.out
        else AttributeError:
            return None

    def construir(self, atividades):
        self.root = root_config(self.fechar, '%s - Prioridades' % TITLE)

        msg = u'Use os botões "Subir" e "Descer" para ordenar as atividades ' \
              'listadas abaixo por ordem descrescente de prioridade (mais ' \
              'importantes primeiro).'
        msglbl = tk.Label(self.root, text=msg, wraplength=400,
                          justify=tk.LEFT)
        msglbl.pack()

        ordenaframe = tk.Frame(self.root)
        ordenaframe.pack(expand=True, fill=tk.BOTH)

        listboxframe = tk.Frame(ordenaframe)
        listboxframe.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

        self.listbox = tk.Listbox(listboxframe)
        self.listbox.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        for atividade in atividades:
            self.listbox.insert(tk.END, atividade)
        self.listbox.select_set(0)
        # TODO: descobrir como setar a posição do maldito retângulo

        scrollbar = tk.Scrollbar(listboxframe, orient=tk.VERTICAL,
                                       command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.LEFT, fill=tk.Y)

        controleframe = tk.Frame(ordenaframe)
        controleframe.pack(side=tk.LEFT, expand=False, anchor=tk.N)

        subirbtn = tk.Button(controleframe, command=self.subirbtn_cb,
                             text='Subir')
        subirbtn.pack(fill=tk.X)

        descerbtn = tk.Button(controleframe, command=self.descerbtn_cb,
                              text='Descer')
        descerbtn.pack(fill=tk.X)

        dialogobtnsframe = tk.Frame(self.root)
        dialogobtnsframe.pack(anchor=tk.E)

        cancelarbtn = tk.Button(dialogobtnsframe, command=self.fechar,
                                text='Cancelar')
        cancelarbtn.pack(side=tk.RIGHT)

        okbtn = tk.Button(dialogobtnsframe, command=self.okbtn_cb, text='OK')
        okbtn.pack(side=tk.RIGHT)

    def swapitems(self, x, y):
        '''Troca a posição do item no índice x com o item no índice y.'''
        self.listbox.insert(x, self.listbox.get(y))
        self.listbox.delete(y+1)

    def subirbtn_cb(self):
        cur = int(self.listbox.curselection()[0])
        if cur:
            self.swapitems(cur-1, cur)
        self.listbox.select_set(cur-1)
        self.listbox.see(cur-1)

    def descerbtn_cb(self):
        cur = int(self.listbox.curselection()[0])
        if cur < (self.listbox.size() - 1):
            self.swapitems(cur, cur+1)
        self.listbox.select_set(cur+1)
        self.listbox.see(cur+1)

    def okbtn_cb(self):
        self.out = []
        for i in range(self.listbox.size()):
            self.out.append(self.listbox.get(i))
        self.fechar()

    def fechar(self):
        self.root.quit()
        self.root.destroy()

def cronometro_dialog(atividade, parar=True):
    '''cronometroDialog(atividade) -> float

    Fábrica de janelas de cronômetro. Retorna o tempo decorrido em horas desde a
    chamada da função. parar determina se o cronômetro deve parar quanto o tempo
    decorrido for igual ao saldo da atividade.'''
    d = CronometroDialog(atividade, parar)
    if atividade.saldo == d.cronometro.decorridoh:
        raise FimAlcancado
    return d.cronometro.decorridoh


def horaspin(msg):
    h = HoraSpinDialog(msg)
    return h.get()

def prioridade_dialog(atividades):
    p = PrioridadeDialog(atividades)
    return p.get()

def notificar(msg):
    '''Exibe uma janela de diálogo com a mensagem em msg.'''
    eg.msgbox(msg, TITLE)


def perguntar(pergunta):
    '''perguntar(pergunta) -> bool

    Exibe uma janela com uma pergunta do tipo sim ou não e retorna a resposta
    como bool.'''
    return bool(eg.ynbox(pergunta, TITLE))


def entrar(msg, inteiro=False):
    '''entrar(msg) -> str

    Exibe uma janela com a mensagem em msg e uma caixa de texto para que o
    usuário informe alguma string.'''
    if inteiro:
        return eg.integerbox(msg, TITLE, upperbound=168) # há 168h em uma semana
    return eg.enterbox(msg, TITLE)


def escolher(msg, opcoes):
    '''escolher(msg, opcoes) -> opção

    Exibe uma janela que permite que o usuário escolha uma dentre várias opções
    e retorna a opção escolhida.'''
    return eg.choicebox(msg, TITLE, opcoes)


def menu(msg, botoes):
    '''menu(msg, botoes) -> botoes[i]

    Exibe uma janela com uma mensagem e vários botões, retornando o texto
    contido no botão pressionado pelo usuário.'''
    return eg.buttonbox(msg, TITLE, botoes)


def escolher_arquivo(msg, extensao):
    '''escolher_arquivo(msg, extensao) -> str

    Exibe uma janela para que o usuário escolha um arquivo e retorna o path
    completo para o arquivo escolhido.'''
    return eg.fileopenbox(msg, TITLE, '*.' + extensao)
