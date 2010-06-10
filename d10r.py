#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
Um utilitário para pessoas enroladas.

O d10r permite que você defina atividades, quanto tempo disponível tem
para realizá-las e atribua prioridades a elas, de acordo com as suas
respostas a um questionário. Feito isso, o d10r calcula por quanto tempo
você deve se ocupar com esta atividade semanalmente e conta o tempo que
você já "pagou".

Copyright (C) 2010  Ygor Mutti
Licenciado sob GPLv3, com texto disponível no arquivo COPYING
'''

__author__ = 'Ygor Mutti <ygormutti@dcc.ufba.br>'
__version__ = '0.1alpha'

from ConfigParser import SafeConfigParser, NoSectionError
import os
import time
import shutil
import codecs
import datetime
import threading
import easygui as eg
import Tkinter as tk

CONFIG = os.path.expanduser('~/.d10r')
HEADER = '__header__'
TITLE = 'd10r'
ENCODING = 'utf-8'

class FimAlcancadoWarning(Warning):
    pass

class ArquivoError(Exception):
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

class CronometroDialog:
    '''Janela que exibe o nome de uma atividade, o tempo decorrido, o saldo e
    botões para que o usuário pause ou pare o cronômetro.'''
    __refresh_time = 200
    def __init__(self, atividade, root, parar=True):
        self.atividade = atividade
        if parar:
            self.cronometro = Cronometro(atividade.saldo, True)
        else:
            self.cronometro = Cronometro(None)
        self.root = root
        self.construir()

    def start(self):
        if not self.cronometro.isAlive():
            self.cronometro.start()
        self._refresh()
    
    def _refresh(self):
        self.tempoDecorridoLbl.config(text=formatah(-self.cronometro.decorridoh,
                                      segundos=True))
        if not self.cronometro.isparado:
            self.tempoDecorridoLbl.after(self.__refresh_time, self._refresh)
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
        self.root.title('%s - Atividade: %s' % (TITLE, self.atividade.nome))
        self.root.protocol('WM_DELETE_WINDOW', self.pararCb)
        self.root.iconname(TITLE)
        self.root.wm_attributes('-topmost', 1)

        ### Frames ###
        
        mainFrame = tk.Frame(self.root)
        mainFrame.pack()

        ### Labels ###
        
        atividadeLabel = tk.Label(mainFrame, text='Decorrido/Saldo: ', justify='left')
        atividadeLabel.pack(side='left', expand=True)

        self.tempoDecorridoLbl = tk.Label(mainFrame,
                                 text=formatah(self.cronometro.decorridoh, True, False))
        self.tempoDecorridoLbl.pack(side='left', expand=True)
        
        tempoSaldoLbl = tk.Label(mainFrame,
                                 text='/ ' + formatah(self.atividade.saldo, False, True))
        tempoSaldoLbl.pack(side='left', expand=True)

        ### Buttons ###
        pausarBtn = tk.Checkbutton(mainFrame, text='Pausar', command=self.pausarCb)
        pausarBtn.pack(side='left')

        pararBtn = tk.Button(mainFrame, text='Finalizar', command=self.pararCb)
        pararBtn.pack(side='left')

class HoraSpinDialog:
    def __init__(self, msg):
        self.msg = msg
        self.construir()
        self.root.mainloop()

    def get(self):
        try:
            return (self.horas, self.minutos, self.segundos)
        except NameError:
            return None

    def construir(self):
        self.root = tk.Tk()
        self.root.protocol('WM_DELETE_WINDOW', self.fechar)

        msglbl = tk.Label(self.root, text=self.msg)
        msglbl.pack()

        formframe = tk.Frame(self.root)
        formframe.pack()

        lblsframe = tk.Frame(formframe)
        lblsframe.pack(side='left')

        spinsframes = tk.Frame(formframe)
        spinsframes.pack(side='left')

        horalbl = tk.Label(lblsframe, text='Horas: ')
        horalbl.pack()

        minutolbl = tk.Label(lblsframe, text='Minutos: ')
        minutolbl.pack()

        segundolbl = tk.Label(lblsframe, text='Segundos: ')
        segundolbl.pack()

        self._horaspn = tk.Spinbox(spinsframes, values=range(100))
        self._horaspn.pack()

        self._minutospn = tk.Spinbox(spinsframes, values=range(100))
        self._minutospn.pack()

        self._segundospn = tk.Spinbox(spinsframes, values=range(100))
        self._segundospn.pack()        

        okbtn = tk.Button(self.root, text='OK', command=self.okbtn_cb)
        okbtn.pack()

    def okbtn_cb(self):
        self.horas = int(self._horaspn.get())
        self.minutos = int(self._minutospn.get())
        self.segundos = int(self._segundospn.get())
        self.fechar()

    def fechar(self):
        self.root.quit()
        self.root.destroy()

class Collection(type):
    '''Metaclass used to register classes instances.'''

    def __init__(cls, name, base, dict):
        '''Called when the class is instantiated (declared).'''
        super(Collection, cls).__init__(name, base, dict)

        cls.__all = []

        @classmethod
        def __all__(cls):
            '''Returns a list containing all instances of the class.'''
            return cls.__all

        @classmethod
        def __clear__(cls):
            cls.__all = []

        cls.__all__ = __all__
        cls.__clear__ = __clear__

    def __call__(cls, *args, **kwargs):
        '''Creates new instances and append them to __all__.'''
        obj = super(Collection, cls).__call__(*args, **kwargs)
        cls.__all.append(obj)
        return obj

class Atividade(object):
    __metaclass__ = Collection

    def __init__(self, nome, pts, saldo):
        '''nome -> str
        pts -> float
        saldo -> float'''
        self.nome = nome
        self.pts = pts
        self.saldo = saldo

    def creditarh(self, toth, nvezes=1):
        '''Método chamado, semanalmente, para creditar horas em atividades, de
        acordo com a qtd. de horas disponíveis.'''
        self.saldo += (nvezes * (self.pts * (toth * 1.0)))

    def debitarh(self, horas):
        '''Diminui o saldo da atividade em horas.'''
        self.saldo -= horas

def combinar2(itens):
    '''combinar2(itens) -> lista de tuplas

    Gera combinações simples dos itens tomados 2 a 2, sem repetições ou
    combinações com a ordem trocada.'''
    combinacoes = []
    for a in itens:
        for b in itens:
            if a != b:
                par = set()
                par.add(a); par.add(b)
                for p in combinacoes:
                    if not p.difference(par): # se p for igual a par
                        break
                else:
                    combinacoes.append(par)

    for i, p in enumerate(combinacoes):
        combinacoes[i] = tuple(p)

    combinacoes.sort(key=lambda x: x[0] + x[1])
    return combinacoes

def init():
    '''Inicializa o arquivo de configuração do d10r.'''
    notificar('Obrigado por usar o d10r (este programa que vos fala).\n' +
              'A seguir eu farei algumas perguntas para que eu possa te ajudar' +
              ' a gerenciar o tempo que você deve gastar com cada atividade da' +
              ' sua rotina. Muita produtividade pra você!')
    atividades = ler_atividades()
    pares = combinar2(atividades)

    prioridades = {}
    for i in atividades:
        prioridades[i] = 1

    for p in pares:
            opcao = escolher('Defina suas prioridades.\n' +
                             'Qual é mais importante?', p)
            if not opcao:
                notificar('Se você não sabe, não sou eu quem vai saber.' +
                          '\nMe execute de novo quando decidir. ;)')
                raise SystemExit(1)
            prioridades[opcao] += 1

    toth = entrar('Quantas horas semanais você deseja administrar?', True)
    if not toth:
        notificar('Se não é pra administrar horas, pra quê você me quer? =|' +
                  '\nTchau!')
        raise SystemExit(1)

    referencial = sum(prioridades.values())

    for nome in atividades:
        if nome != HEADER:
            pts = (prioridades[nome] * 1.0) / referencial
            Atividade(nome, pts, 0)
        else:
            notificar('Atividade %s ignorada.' % (HEADER))


    salvar_config(toth, datetime.date.today().isoweekday(), 0)

    notificar('Configurações salvas com sucesso.')
    # TODO: aproveitar os saldos de atividades com nomes coincidentes

def parse_config():
    '''parse_config() -> (toth, inicio, timestamp)
    toth -> int
    inicio -> int
    timestamp -> datetime.date

    Analisa o arquivo em CONFIG e retorna o total de horas disponíveis, o dia da
    semana de início da contagem (no formato ISO) e a data do último crédito de
    horas, além de instanciar as atividades.'''
    parser = SafeConfigParser()

    try:
        parser.readfp(codecs.open(CONFIG, 'r', ENCODING))
    except IOError:
        raise ArquivoError('Nenhum arquivo de configuração encontrado.')

    try:
        toth = parser.getint(HEADER, 'disponivel')
        inicio = parser.getint(HEADER, 'inicio')
        timestamp = parser.getint(HEADER, 'timestamp')

        if timestamp:
            ano, timestamp = divmod(timestamp, 10000)
            mes, dia = divmod(timestamp, 100)
            timestamp = datetime.date(ano, mes, dia)

        for a in parser.sections():
            if a != HEADER:
                kwargs = {'nome':a, 'pts':parser.getfloat(a, 'pts'),
                          'saldo':parser.getfloat(a, 'saldo')}
                Atividade(**kwargs)
    except (TypeError, NoSectionError):
        raise ArquivoError('Arquivo de configuração corrompido.')

    return (toth, inicio, timestamp)

def salvar_config(toth, inicio, timestamp):
    '''salvar_config(toth, inicio, timestamp)
    toth -> int
    inicio -> int
    timestamp -> datetime.date

    Atualiza CONFIG de forma análoga a função parse_config().'''
    if isinstance(timestamp, (datetime.date, datetime.datetime)):
        timestamp = timestamp.year * 10000 + \
                    timestamp.month * 100 + timestamp.day

    parser = SafeConfigParser()
    parser.add_section(HEADER)

    # Campos das atividades
    # pts: porcentagem de prioridade
    # saldo: quando positivo indica quantas horas precisam ser pagas
    for a in Atividade.__all__():
        parser.add_section(a.nome)
        parser.set(a.nome, 'pts', str(a.pts))
        parser.set(a.nome, 'saldo', str(a.saldo))

    # Seção HEADER
    # disponivel: base para calcular as prestações de cada atividade
    # inicio: dia da semana em que as horas são creditadas
    # timestamp: fim da última execução do programa
    parser.set(HEADER, 'disponivel', `toth`)
    parser.set(HEADER, 'inicio', `inicio`)
    parser.set(HEADER, 'timestamp', `timestamp`)

    cfg = codecs.open(CONFIG, 'w', ENCODING)
    parser.write(cfg)

def dias_ate_prox_dia(dia, x):
    '''dias_ate_prox_dia(dia, x) -> int
    
    Determina quantos dias faltam, a partir de x (um dia da semana), para dia
    (outro dia da semana). Os dias devem estar no formato ISO para dia da semana.'''
    if dia == x:
        return 0
    elif dia < x:
        return (7 + dia - x)
    else:
        return (dia - x)

def dias_x_entre(dia, antes, depois):
    '''dias_x_entre(dia, antes, depois) -> int
    
    Determina quantas vezes ocorre um dia da semana entre duas datas.'''
    delta = depois - antes
    div, mod = divmod(delta.days, 7)
    n = div
    if (mod >= dias_ate_prox_dia(dia, antes.isoweekday())) and (mod != 0):
        n += 1
    return n

def creditar_tudo(toth, inicio, timestamp):
    '''Verifica se existem horas a serem creditadas nas atividades e credita-as.'''
    if timestamp == 0: # primeira execução após init
        vezes = 1
    else:
        vezes = dias_x_entre(inicio, timestamp, datetime.date.today())
        # se o timestamp corresponde ao dia da semana de inicio da contagem
        # a funcao dias_x_entre contará, além do esperado, o próprio dia do
        # timestamp, sendo que as horas daquele dia já foram creditadas, daí:
        if timestamp.isoweekday() == inicio:
        	vezes -= 1
    for a in Atividade.__all__():
        a.creditarh(toth, vezes)

    return bool(vezes)

def formatah(horas, segundos=False, sinal=True):
    '''formatah(horas, segundos=False, sinal=True) -> '[+-]HH:MM[:SS]'
    
    Recebe uma quantidade de horas como float e retorna uma string HH:MM.'''
    if sinal:
        sinal = '-' if (horas < 0) else '+'
    else:
        sinal = ''
    s = abs(horas) * 3600.0
    m, s = divmod(s, 60.0)
    h, m = divmod(m, 60.0)
    
    if segundos:
        return '%s%02d:%02d:%02d' % (sinal, int(h), int(m), int(s))
    else:
        return '%s%02d:%02d' % (sinal, int(h), int(m))

def escolher_ativ():
    '''escolher_ativ() -> atividade
    
    Exibe as atividades cadastradas, o saldo de horas e espera que o usuário
    informe qual delas deseja começar.'''
    atividades = sorted(Atividade.__all__(), key=lambda x: x.saldo, reverse=True)

    opcoes = []
    for i, a in enumerate(atividades):
        opcoes.append('%d- %s (Saldo: %s)' % (i, a.nome, formatah(a.saldo)))

    opcao = escolher('Qual atividade deseja iniciar?', opcoes)

    if opcao:
        return atividades[int(opcao.split('-')[0])]
    else:
        return None

def horaspin(msg):
    h = HoraSpinDialog(msg)
    return h.get()

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
        return eg.integerbox(msg, TITLE)
    return eg.enterbox(msg, TITLE)

def ler_atividades():
    '''ler_atividades(msg) -> lista de entradas

    Exibe uma janela para que o usuário entre com o nome das atividades.'''
    entradas = []
    while True:
        msg = 'Informe uma nova atividade ou cancele para continuar.'
        if entradas:
            complemento = u'\nAs seguintes atividades já foram adicionadas:\n'
            atividades = '\n'.join([' - ' + e for e in entradas])
            msg += complemento + atividades

        entrada = entrar(msg)
        if entrada:
            entradas.append(entrada)
            entradas = list(set(entradas)) # remove duplicadas
        else: # cancelar foi pressionado
            if len(entradas) >= 2:
                return set(entradas)
            else:
                notificar('É preciso informar ao menos duas atividades.' +
                          '\nVocê é monotarefa?')
                raise SystemExit(1)

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

def menu_cfg(msg):
    '''Exibe um diálogo com opções para procurar e copiar um arquivo de
    configuração do d10r, criar um novo arquivo e sair do programa.'''
    botoes = ('Novo', 'Procurar', 'Sair')
    global CONFIG
    msg += '''

O que deseja fazer?
%s: Criar um novo arquivo
%s: Utilizar um outro arquivo
%s: Sair do programa''' % tuple(botoes)

    botao = menu(msg, botoes)

    if botao == botoes[0]:
        init()
    elif botao == botoes[1]:
        caminho = escolher_arquivo('Escolha o arquivo desejado', 'cfg')
        if caminho:
            if perguntar('O arquivo selecionado está fora do local padrão, ' +
                         'de forma que o programa sempre perguntará por ele ' +
                         'quando iniciar. Deseja copiar o arquivo para o local ' +
                         'padrão?\n\nSe sim, você precisará fazer backup do arquivo ' +
                         'sempre que for utilizá-lo em outro computador.'):
                shutil.copy2(caminho, CONFIG)
                notificar('Arquivo copiado com sucesso!')
            else:
                CONFIG = caminho
        else:
            notificar('Preciso do arquivo de configuração para continuar!')
    else:
        raise SystemExit(0)

def cronometro_dialog(atividade, parar=True):
    '''cronometroDialog(atividade) -> float
    
    Fábrica de janelas de cronômetro. Retorna o tempo decorrido em horas desde a
    chamada da função. parar determina se o cronômetro deve parar quanto o tempo
    decorrido for igual ao saldo da atividade.'''
    root = tk.Tk()
    d = CronometroDialog(atividade, root, parar)
    d.start()
    root.mainloop()
    if atividade.saldo == d.cronometro.decorridoh:
        raise FimAlcancadoWarning
    return d.cronometro.decorridoh

def debitar(atividade, parar=True):
    c = 'Cronômetro'
    op = menu('Deseja iniciar o cronômetro ou inserir diretamente a quantidade ' +
              'de horas cumpridas diretamente?', (c, 'Inserir'))
    
    if op == c:
        return cronometro_dialog(atividade, parar)
    else:
        try:
            h, m, s = horaspin('Debitar:')
            h += (m / 60.0) + (s / 3600.0)
            return h
        except TypeError:
            return 0.0

def main():
    '''Rotina principal do programa.'''
    while True:
        try:
            Atividade.__clear__()
            toth, inicio, timestamp = parse_config()
            break
        except ArquivoError, e:
            menu_cfg(str(e))

    while True:
    	if (not timestamp) or (datetime.date.today() > timestamp):
			if creditar_tudo(toth, inicio, timestamp):
			    # guarda a data do último crédito
			    timestamp = datetime.date.today()

        debito = 0
        try:
            atividade = escolher_ativ()

            if atividade.saldo > 0:
                debito = debitar(atividade)
            else:
                if perguntar('Esta atividade não possui mais horas a serem' +
                             ' cumpridas.\nDeseja continuar mesmo assim?'):
                    debito = debitar(atividade, False)
        except FimAlcancadoWarning:
            debito = atividade.saldo
            notificar('Você acabou de cumprir as horas da atividade:\n' +
                      atividade.nome)
        except AttributeError, e: # usuário clicou em Sair, ou não... =/
            break
        finally:
            if debito and perguntar('Confirma %s horas gastas com %s?' %
                         (formatah(debito), atividade.nome)):
                atividade.debitarh(debito)
            salvar_config(toth, inicio, timestamp)

if __name__ == '__main__':
    main()
