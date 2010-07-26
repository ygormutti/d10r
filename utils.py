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
