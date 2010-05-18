#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
Um utilitário para pessoas enroladas.

O d10r permite que você defina atividades, quanto tempo disponível tem
para realizá-las e atribua prioridades a elas, de acordo com as suas
respostas a um questionário. Feito isso, o d10r calcula por quanto tempo
você deve se ocupar com esta atividade semanalmente e conta o tempo que
você já "pagou".

Licenciado sob CC-BY-SA, com texto disponível em:
http://creativecommons.org/licenses/by-sa/3.0/br/
'''

__author__ = 'Ygor Mutti <ygormutti@dcc.ufba.br>'
__version__ = 'pre-pre-alpha 0.0.2'

from ConfigParser import SafeConfigParser
import os
import time
import shutil
import datetime
import threading
import easygui as eg
import Tkinter as tk

CONFIG = os.path.expanduser('~/d10r_eg.cfg')
HEADER = '__header__'
TITLE = 'd10r'

class FimAlcancadoWarning(Warning):
    pass

class ArquivoError(Exception):
    pass

class Cronometro(threading.Thread):
    '''Implementação da função cronometrar() com threads.'''
    def __init__(self, fim=None):
        threading.Thread.__init__(self)
        self.fim = fim
        self._decorrido = 0
        self._pausado = False
        self._parado = False
    def run(self):
        while True:
            if self.fim != None and self.decorrido >= self.fim:
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
        '''Encerra a contagem e finaliza a thread. Retorna o tempo decorrido.'''
        self._parado = True
    @property
    def decorrido(self):
        '''Tempo em segundos decorrido desde o início da contagem.'''
        return self._decorrido
    @property
    def decorridoh(self):
        '''Mesmo que decorrido, porém retorna o valor em horas.'''
        return self._decorrido / 3600.0

class CronometroFrame(Cronometro, tk.Frame):
    '''Janela que exibe o nome de uma atividade, o tempo decorrido, o saldo e
    botões para que o usuário pause ou pare o cronometro.'''
    def __init__(self, ativ, saldo, fim=None):
        Cronometro.__init__(self, fim)
        self.ativ = ativ
        self.saldo = saldo
    
    def run(self):
        Cronometro.run(self)
        

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
        self.saldo += (nvezes * (self.pts * (toth*1.0)))

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

    combinacoes.sort(key=lambda x: x[0]+x[1])
    return combinacoes

def init():
    '''Inicializa o arquivo de configuração do d10r.'''
    notificar('Obrigado por usar o d10r (este programa que vos fala).\n' +
              'A seguir eu farei algumas perguntas para que eu possa te ajudar'+
              ' a gerenciar o tempo que você deve gastar com cada atividade da'+
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

    toth = int(entrar('Quantas horas semanais você deseja administrar?'))
    if not toth:
        notificar('Se não é pra administrar horas, pra quê você me quer? =|'+
                  '\nTchau!')
        raise SystemExit(1)

    referencial = sum(prioridades.values())

    for nome in atividades:
        if nome != HEADER:
            pts = (prioridades[nome] * 1.0) / referencial
            Atividade(nome, pts, 0)
        else:
            notificar('Atividade %s ignorada.' % (HEADER))


    salvar_config(toth, datetime.date.today().isoweekday(),0)

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

    if not parser.read(CONFIG):
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
                kwargs = {'nome':a, 'pts':parser.getfloat(a,'pts'),
                          'saldo':parser.getfloat(a,'saldo')}
                Atividade(**kwargs)
    except TypeError:
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

    cfg = file(CONFIG, 'w')
    parser.write(cfg)

def dias_ate_prox_dia(dia, x):
    '''Determina quantos dias faltam, a partir de x (um dia da semana), para dia
    (outro dia da semana). Os dias devem estar no formato ISO para dia da semana.'''
    if dia == x:
        return 0
    elif dia < x:
        return (7 + dia - x)
    else:
        return (dia - x)

def dias_x_entre(dia, antes, depois):
    '''Determina quantas vezes ocorre um dia da semana entre duas datas.'''
    delta = depois - antes
    div, mod = divmod(delta.days, 7)
    n = div
    if (mod >= dias_ate_prox_dia(dia, antes.isoweekday())) and (mod != 0):
        n += 1
    return n

def creditar_tudo(toth,inicio,timestamp):
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

def formatah(horas):
    '''Recebe uma quantidade de horas como float e retorna uma string HH:MM.'''
    sinal = '-' if (horas < 0) else '+'
    minutos = int(abs(horas) * 60)
    horas, minutos = divmod(minutos, 60)
    return '%s%d:%02d' % (sinal, horas, minutos)

def escolher_ativ():
    '''Exibe as atividades cadastradas, o saldo de horas e espera que o usuário
    informe qual delas deseja começar.'''
    atividades = sorted(Atividade.__all__(), key=lambda x: x.saldo, reverse=True)

    opcoes = []
    for i,a in enumerate(atividades):
        opcoes.append('%d- %s (Saldo: %s)' % (i, a.nome, formatah(a.saldo)))

    opcao = escolher('Qual atividade deseja iniciar?', opcoes)

    if opcao:
        return atividades[int(opcao.split('-')[0])]
    else:
        return None

def cronometrar(fim=None):
    '''cronometrar(fim=None) -> int

    De forma síncrona conta quantos segundos se passaram desde que for chamada.
    O usuário interrompe a contagem ao pressionar Ctrl-C. Se fim for fornecido,
    para de contar assim que alcancar fim segundos, lançando FimAlcancadoWarning.'''
    decorrido = 0
    try:
        if fim != None:
            while fim >= decorrido:
                time.sleep(1)
                decorrido += 1
            raise FimAlcancadoWarning
        else:
            while True:
                time.sleep(1)
                decorrido += 1
    except KeyboardInterrupt:
        return decorrido

def cronometrarh(fim=None):
    '''cronometrarh(fim=None) -> int

    O mesmo que cronometrar(), mas recebe e retorna o tempo decorrido em horas.'''
    if fim != None:
        return cronometrar(fim * 3600.0) / 3600.0
    else:
        return cronometrar() / 3600.0

def notificar(msg):
    '''Exibe uma janela de diálogo com a mensagem em msg.'''
    eg.msgbox(msg, TITLE)

def perguntar(pergunta):
    '''Exibe uma janela com uma pergunta do tipo sim ou não e retorna a resposta
    como bool.'''
    return bool(eg.ynbox(pergunta,TITLE))


def entrar(msg):
    '''Exibe uma janela com a mensagem em msg e uma caixa de texto para que o
    usuário informe alguma string.'''
    return eg.enterbox(msg,TITLE)

def ler_atividades():
    '''ler_atividades(msg) -> lista de entradas

    Exibe uma janela para que o usuário entre com o nome das atividades.'''
    entradas = []
    while True:
        msg = 'Informe uma nova atividade ou cancele para continuar.'
        if entradas:
            complemento = '\nAs seguintes atividades já foram adicionadas:\n'
            atividades = '\n'.join(['- ' + e for e in entradas])
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

def menu(msg,botoes):
    '''Exibe uma janela com uma mensagem e vários botões, retornando o texto
    contido no botão pressionado pelo usuário.'''
    return eg.buttonbox(msg,TITLE,botoes)

def escolher_arquivo(msg, extensao):
    '''Exibe uma janela para que o usuário escolha um arquivo e retorna o path
    completo para o arquivo escolhido.'''
    return eg.fileopenbox(msg, TITLE, '*.'+extensao)

def menu_cfg(msg):
    botoes = ('Novo', 'Procurar', 'Sair')
    msg += '''

O que deseja fazer?
%s: Criar um novo arquivo
%s: Utilizar um outro arquivo
%s: Sair do programa''' % tuple(botoes)

    botao = menu(msg, botoes)

    if botao == botoes[0]:
        init()
    elif botao == botoes[1]:
        caminho = escolher_arquivo('Escolha o arquivo desejado','cfg')
        if caminho:
            shutil.copy2(caminho, CONFIG)
            notificar('Arquivo copiado com sucesso!')
        else:
            notificar('Preciso do arquivo de configuração para continuar!')
    else:
        raise SystemExit(0)

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
			if creditar_tudo(toth,inicio,timestamp):
			    # guarda a data do último crédito
			    timestamp = datetime.date.today()
    	
        debito = 0
        try:
            atividade = escolher_ativ()

            if atividade.saldo > 0:
                debito = cronometrarh(atividade.saldo)
            else:
                if perguntar('Esta atividade não possui mais horas a serem' +
                             ' cumpridas.\nDeseja continuar mesmo assim?'):
                    debito = cronometrarh()
        except FimAlcancadoWarning:
            debito = atividade.saldo
            notificar('Você acabou de cumprir as horas da atividade:\n' +
                      atividade.nome)
        except AttributeError: # usuário clicou em Sair
            break
        finally:
            if debito and perguntar('Confirma %s horas gastas com %s?' %
                         (formatah(debito), atividade.nome)):
                atividade.debitarh(debito)

    salvar_config(toth, inicio, timestamp)

if __name__ == '__main__':
    main()
