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

__author__ = 'Ygor Mutti <mamutti@icaju.com>'
__version__ = '0.1'


import shutil
import datetime

import gui
import data
from utils import formatah


def calcula_prioridades(atividades):
    '''calcula_prioridades(atividades) -> dict

    Calcula os pontos de prioridade a partir de uma lista com nomes de
    atividades ordenada por ordem decrescente de prioridade.'''
    out = {}
    for i,a in enumerate(atividades):
        out[a] = len(atividades) - i
    return out


def init():
    '''Inicializa o arquivo de configuração do d10r.'''
    gui.notificar('Obrigado por usar o d10r (este programa que vos fala).\n' +
              'A seguir eu farei algumas perguntas para que eu possa te ajudar' +
              ' a gerenciar o tempo que você deve gastar com cada atividade da' +
              ' sua rotina. Muita produtividade pra você!')
    atividades = ler_atividades()

    ordprioridade = gui.prioridade_dialog(atividades)

    if not ordprioridade:
        gui.notificar('Se você não sabe, não sou eu quem vai saber.' +
                  '\nMe execute de novo quando decidir. ;)')
        raise SystemExit(1)

    prioridades = calcula_prioridades(ordprioridade)

    toth = gui.entrar('Quantas horas semanais você deseja administrar?', True)
    if not toth:
        gui.notificar('Se não é pra administrar horas, pra quê você me quer?' +
                  ' =|\nTchau!')
        raise SystemExit(1)

    acumular = gui.perguntar(
        'As horas não cumpridas devem se acumular de uma semana para a outra?' +
        '\n\nAcumular horas é útil apenas se você deve cumprir rigorosamente' +
        ' a quantidade de horas estipulada. Caso contrário, apenas as horas ' +
        'cumpridas a mais (se houver) serão acumuladas.')

    referencial = sum(prioridades.values())

    for nome in atividades:
        pts = (prioridades[nome] * 1.0) / referencial
        data.Atividade(nome, pts, 0)

    inicio = datetime.date.today().isoweekday()

    data.creditar_tudo(toth, inicio, 0, acumular)
    data.salvar_config(toth, inicio, datetime.date.today(), acumular)

    gui.notificar('Configurações salvas com sucesso.')


def escolher_ativ():
    '''escolher_ativ() -> atividade

    Exibe as atividades cadastradas, o saldo de horas e espera que o usuário
    informe qual delas deseja começar.'''
    atividades = sorted(data.Atividade.all(), key=lambda x: x.saldo, reverse=True)

    opcoes = []
    for i, a in enumerate(atividades):
        opcoes.append('%d- %s (Saldo: %s)' % (i, a.nome, formatah(a.saldo)))

    opcao = gui.escolher('Qual atividade deseja iniciar?', opcoes)

    if opcao:
        return atividades[int(opcao.split('-')[0])]
    else:
        return None


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

        entrada = gui.entrar(msg)
        if entrada:
            entradas.append(entrada)
            entradas = list(set(entradas)) # remove duplicadas
        else: # cancelar foi pressionado
            if len(entradas) >= 2:
                return set(entradas)
            else:
                gui.notificar('É preciso informar ao menos duas atividades.' +
                          '\nVocê é monotarefa?')
                raise SystemExit(1)


def menu_cfg(msg):
    '''Exibe um diálogo com opções para procurar e copiar um arquivo de
    configuração do d10r, criar um novo arquivo e sair do programa.'''
    botoes = ('Novo', 'Procurar', 'Sair')
    data.CONFIG
    msg += '''

O que deseja fazer?
%s: Criar um novo arquivo
%s: Utilizar um outro arquivo
%s: Sair do programa''' % tuple(botoes)

    botao = gui.menu(msg, botoes)

    if botao == botoes[0]:
        init()
    elif botao == botoes[1]:
        caminho = gui.escolher_arquivo('Escolha o arquivo desejado', 'cfg')
        if caminho:
            if gui.perguntar('O arquivo selecionado está fora do local padrão, ' +
                         'de forma que o programa sempre perguntará por ele ' +
                         'quando iniciar. Deseja copiar o arquivo para o local ' +
                         'padrão?\n\nSe sim, você precisará fazer backup do arquivo ' +
                         'sempre que for utilizá-lo em outro computador.'):
                shutil.copy2(caminho, data.CONFIG)
                gui.notificar('Arquivo copiado com sucesso!')
            else:
                data.CONFIG = caminho
        else:
            gui.notificar('Preciso do arquivo de configuração para continuar!')
    else:
        raise SystemExit(0)


def debitar(atividade, parar=True):
    c = 'Cronômetro'
    op = gui.menu('Deseja iniciar o cronômetro ou inserir a quantidade ' +
              'de horas cumpridas diretamente?', (c, 'Inserir'))

    if op == c:
        return gui.cronometro_dialog(atividade, parar)
    else:
        try:
            h, m, s = gui.horaspin('Atividade: %s' % atividade.nome)
            h += (m / 60.0) + (s / 3600.0)
            return h
        except TypeError:
            return 0.0


def main():
    '''Rotina principal do programa.'''
    while True:
        data.Atividade.clear()
        try:
            toth, inicio, timestamp, acumular = data.parse_config()
            break
        except data.ArquivoError, e:
            menu_cfg(str(e))

    while True:
        if (not timestamp) or (datetime.date.today() > timestamp):
            if data.creditar_tudo(toth, inicio, timestamp, acumular):
                # guarda a data do último crédito
                timestamp = datetime.date.today()

        debito = 0
        try:
            atividade = escolher_ativ()

            if atividade.saldo > 0:
                debito = debitar(atividade)
            else:
                if gui.perguntar('Esta atividade não possui mais horas a serem' +
                             ' cumpridas.\nDeseja continuar mesmo assim?'):
                    debito = debitar(atividade, False)
        except gui.FimAlcancado:
            debito = atividade.saldo
            gui.notificar(u'Você acabou de cumprir as horas da atividade:\n' +
                      atividade.nome)
        except AttributeError, e: # usuário clicou em Sair, ou não... =/
            break
        finally:
            if debito and gui.perguntar(u'Confirma %s horas gastas com %s?' %
                         (formatah(debito), atividade.nome)):
                atividade.debitarh(debito)
            data.salvar_config(toth, inicio, timestamp, acumular)


if __name__ == '__main__':
    main()
