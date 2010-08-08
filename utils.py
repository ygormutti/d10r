#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
Funções e classes úteis e reutilizáveis

Copyright (C) 2010  Ygor Mutti
Licenciado sob GPLv3, com texto disponível no arquivo COPYING
'''

import sys


WINDOWS = 'win'
LINUX = 'linux'
MAC = 'darwin'


def plataforma():
    '''plataforma() -> str

    Descobre a plataforma em que o programa está rodando. Possíveis retornos são
    WINDOWS, LINUX e MAC.'''
    if sys.platform.startswith('win'):
        return WINDOWS
    elif sys.platform.startswith('darwin'):
        return MAC
    return LINUX


def formatah(horas, segundos=False, sinal=True):
    '''formatah(horas, segundos=False, sinal=True) -> '[+-]HH:MM[:SS]'

    Recebe uma quantidade de horas como float e retorna uma string HH:MM.'''
    if sinal and horas:
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
