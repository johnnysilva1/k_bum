#!/usr/bin/env python

from concurrent.futures import ThreadPoolExecutor
import threading
import requests
from bs4 import BeautifulSoup
import time
import os
import sys
import json
import re
import logging
from db_kabum import DB_Kabum


class Bot_Kabum:
    def __init__(self, NOME_DB, DESTINO_LOG, LINKS):

        format = "%(asctime)s - %(levelname)s: %(message)s"
        logging.basicConfig(
            format=format,
            level=logging.ERROR,
            datefmt="%d-%m %H:%M:%S",
            filename=DESTINO_LOG,
            filemode="a",
        )
        logging.info(
            "__init__ " + threading.currentThread().getName(), threading.currentThread()
        )
        self.NOME_DB = NOME_DB
        self.DESTINO_LOG = DESTINO_LOG
        self.LINKS = LINKS

        if not isinstance(LINKS, list):
            logging.error("Os links devem estar em uma lista")
            raise AttributeError

        self.NUM_TRABALHADORES = 2 if len(LINKS) > 1 else 1
        # delay entre requisicoes dos trabalhadores
        self.DELAY = 10
        self.STATUS = {"cod": 0, "msg": "esperando"}

    @staticmethod
    def recebePagina(url):
        try:
            r = requests.get(url)
            # r.raise_for_status()
            return r.text

        except requests.exceptions.RequestException as e:
            logging.error("recebePagina	: Erro ao receber pagina!", exc_info=True)
            print("Erro ao receber pagina: " + str(e))
            return e

    @staticmethod
    def retornaListaDeProdutos(html):
        m = re.search("(?:listagemDados\s=)(\s\[(.*?)\])", html)
        if m:
            return json.loads(m[1])
        else:
            logging.error("Nao foi possivel fazer o parse da pagina")
            return False

    def statusAtual(self):
        return self.STATUS

    def barraProgresso(tempo):
        toolbar_width = 50
        tempo = tempo / 50.0

        # setup toolbar
        sys.stdout.write("[%s]" % (" " * toolbar_width))
        sys.stdout.flush()
        sys.stdout.write("\b" * (toolbar_width + 1))

        for i in xrange(toolbar_width):
            time.sleep(tempo)
            # update the bar
            sys.stdout.write("-")
            sys.stdout.flush()

        sys.stdout.write("]\n")

    # recebe categoria e retorna todas paginas
    def retornaProdutosDaCategoria(self, url, delay_entre_requisicoes):

        listaDeProdutos = list()
        num_pagina = 1
        chegouAoFinal = False

        while not chegouAoFinal:
            endereco = url + "?pagina=" + str(num_pagina) + "&ordem=5&limite=100"

            # !tratar erro caso haja algum problema de rede, dns, acesso etc
            htmlDaPagina = self.recebePagina(endereco)
            produtosDaPagina = self.retornaListaDeProdutos(htmlDaPagina)

            if produtosDaPagina:
                # adiciona os dicionarios na list
                for produto in produtosDaPagina:
                    listaDeProdutos.append(produto)

                num_pagina += 1
                time.sleep(self.DELAY)
            else:
                chegouAoFinal = True

        return listaDeProdutos

    def recebeTodosProdutos(self):
        """
        Cria a pool e passa as urls
        """
        urls = self.LINKS

        futures_list = []
        results = []

        self.STATUS = {"cod": 1, "msg": "recebendo paginas"}

        with ThreadPoolExecutor(max_workers=self.NUM_TRABALHADORES) as executor:
            for url in urls:
                futures = executor.submit(
                    self.retornaProdutosDaCategoria, url, self.DELAY
                )
                futures_list.append(futures)

            for future in futures_list:
                try:
                    result = future.result(timeout=60)
                    results.append(result)
                except Exception as t:
                    logging.error("Erro no futuro")
                    print("Erro no futuro")

        self.STATUS = {"cod": 2, "msg": "paginas recebidas"}
        return results

    def processaResultado(self, produto, indice, hora):

        dadosParaDB = None
        dadosDisponibilidade = None
        ident = produto["codigo"]
        titulo = produto["nome"]
        valor = produto["preco_desconto"]
        nome_fabricante = produto["fabricante"]["nome"]
        cod_fabricante = produto["fabricante"]["codigo"]
        disponibilidade = produto["disponibilidade"]
        is_openbox = produto["is_openbox"]
        tem_frete_gratis = produto["tem_frete_gratis"]
        link = self.LINKS[indice]
        # procura se produto ja existe no banco de dados
        pesquisa = self.DB.procuraProduto(ident)

        # se o prod nao existir preenche o banco de dados com o novo produto
        if len(pesquisa) == 0:
            self.DB.preencheDB(
                ident,
                titulo,
                nome_fabricante,
                cod_fabricante,
                disponibilidade,
                is_openbox,
                tem_frete_gratis,
                link,
            )
            dadosParaDB = [hora, valor, ident]

        else:

            dadosParaDB = [hora, valor, ident]
            # se a disponibilidade mudo
            if disponibilidade != pesquisa[0][4]:
                dadosDisponibilidade = [ident, disponibilidade]

        return dadosParaDB, dadosDisponibilidade

    def iniciaBot(self):
        mensagem = "Escaneando precos kabum"
        os.system('export DISPLAY=:0; notify-send -t 2500 "{}"'.format(mensagem))
        segundos = int(time.time())
        logging.info("iniciaBot	: programa iniciado!")
        # 10800 = 3h*60m*60s
        hora = int(time.time()) - 10800
        logging.info(
            "inciaBot " + threading.currentThread().getName(), threading.currentThread()
        )

        # cria o acesso ao DB aqui usando a mesma thread id da thread principal
        self.DB = DB_Kabum(self.NOME_DB)

        """
		Passa links para pool receber todas paginas
		"""
        resultados = self.recebeTodosProdutos()
        # acumula todos os precos, para ao final salvar no DB
        listaDadosParaDB = list()
        # acumula todas mudancas de disponiblidade e ao final atualiza o DB
        listaDisponibilidade = list()

        for indice, resultado in enumerate(resultados):
            for _ in resultado:
                preco, disponibilidade = self.processaResultado(_, indice, hora)
                listaDadosParaDB.append(preco)
                if disponibilidade:
                    listaDisponibilidade.append(disponibilidade)
        # ao final da categoria, passa lista de dados para funcao salvar no banco
        self.DB.preencheValoresDB(listaDadosParaDB)

        if listaDisponibilidade:
            self.DB.preencheDisponibilidade(listaDisponibilidade)

        logging.info("iniciaBot	: programa terminado!")
        tempo_exec = (int(time.time()) - segundos) / 60
        self.STATUS = {"cod": 3, "msg": str(int(time.time()) - segundos)}
        logging.info("Tempo total " + str(int(time.time()) - segundos) + "s")
        mensagem = "Script kabum.py executado com SUCESSO."
        os.system(
            'export DISPLAY=:0; notify-send -t 10000 "{} {}m"'.format(
                mensagem, tempo_exec
            )
        )


def main():
    links = [
        "https://www.kabum.com.br/hardware/ssd-2-5",
        "https://www.kabum.com.br/computadores/tablets/kindle",
        "https://www.kabum.com.br/hardware/placa-de-video-vga/nvidia",
        "https://www.kabum.com.br/hardware/disco-rigido-hd",
        "https://www.kabum.com.br/celular-telefone/smartphones",
    ]

    links = ["https://www.kabum.com.br/eletronicos/calculadoras"]
    kabum = Bot_Kabum(NOME_DB="DELETA.db", DESTINO_LOG="./kabum.log", LINKS=links)
    kabum.iniciaBot()

    # t = threading.Thread(target=kabum.iniciaBot,name='iniciaOBOT', daemon=False)
    # t.start()
    # print ("main " + threading.currentThread().getName())


if __name__ == "__main__":
    main()
