#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
Módulo de dados (persistência, modelos, etc)

Copyright (C) 2010  Ygor Mutti
Licenciado sob GPLv3, com texto disponível no arquivo COPYING
'''

import os
import codecs
import datetime
from ConfigParser import SafeConfigParser, NoSectionError

from utils import dias_x_entre


CONFIG = os.path.expanduser('~/.d10r')
HEADER = '__header__'
ENCODING = 'utf-8'


class ArquivoError(Exception):
    pass


class Collection(type):
    '''Metaclass used to register classes instances.'''

    def __init__(cls, name, base, dict):
        '''Called when the class is instantiated (declared).'''
        super(Collection, cls).__init__(name, base, dict)

        cls.__all = []

        @classmethod
        def all(cls):
            '''Returns a list containing all instances of the class.'''
            return cls.__all

        @classmethod
        def clear(cls):
            cls.__all = []

        cls.all = all
        cls.clear = clear

    def __call__(cls, *args, **kwargs):
        '''Creates new instances and append them to __all.'''
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


def parse_config():
    '''parse_config() -> (toth, inicio, timestamp, acumular)
    toth -> int
    inicio -> int
    timestamp -> datetime.date
    acumular -> bool

    Analisa o arquivo em CONFIG e retorna o total de horas disponíveis, o dia da
    semana de início da contagem (no formato ISO), a data do último crédito de
    horas e a opção do modo acumulativo, além de instanciar as atividades.'''
    parser = SafeConfigParser()

    try:
        parser.readfp(codecs.open(CONFIG, 'r', ENCODING))
    except IOError:
        raise ArquivoError('Nenhum arquivo de configuração encontrado.')

    try:
        toth = parser.getint(HEADER, 'disponivel')
        inicio = parser.getint(HEADER, 'inicio')
        timestamp = parser.getint(HEADER, 'timestamp')
        acumular = parser.getboolean(HEADER, 'acumular')

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

    return (toth, inicio, timestamp, acumular)


def salvar_config(toth, inicio, timestamp, acumular):
    '''salvar_config(toth, inicio, timestamp, acumular)
    toth -> int
    inicio -> int
    timestamp -> datetime.date
    acumular -> bool

    Atualiza CONFIG de forma análoga a função parse_config().'''
    if isinstance(timestamp, (datetime.date, datetime.datetime)):
        timestamp = timestamp.year * 10000 + \
                    timestamp.month * 100 + timestamp.day

    parser = SafeConfigParser()
    parser.add_section(HEADER)

    # Campos das atividades
    # pts: porcentagem de prioridade
    # saldo: quando positivo indica quantas horas precisam ser pagas
    for a in Atividade.all():
        if a.nome != HEADER:
            # atividades com o mesmo nome do cabeçalho são ignoradas em silêncio
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
    parser.set(HEADER, 'acumular', `acumular`)

    cfg = codecs.open(CONFIG, 'w', ENCODING)
    parser.write(cfg)


def creditar_tudo(toth, inicio, timestamp, acumular):
    '''Verifica se existem horas a serem creditadas nas atividades e credita-as.'''
    if timestamp == 0: # primeira execução após init
        vezes = 1
    else:
        vezes = dias_x_entre(inicio, timestamp, datetime.date.today())
        if vezes and not acumular:
            vezes = 1
        # se o timestamp corresponde ao dia da semana de inicio da contagem
        # a funcao dias_x_entre contará, além do esperado, o próprio dia do
        # timestamp, sendo que as horas daquele dia já foram creditadas, daí:
        if timestamp.isoweekday() == inicio:
        	vezes -= 1
    for a in Atividade.all():
        if a.saldo > 0 and not acumular:
            a.saldo = 0
        a.creditarh(toth, vezes)

    return bool(vezes)
