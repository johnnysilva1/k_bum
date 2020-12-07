#!/usr/bin/env python

from concurrent.futures import ThreadPoolExecutor
import requests
from bs4 import BeautifulSoup
import time
import os
import sys
import json
import re
import logging

from db_kabum import DB_Kabum


def mensagemErro(qtdErros):
	if (qtdErros) >= 10:
		os.system("export DISPLAY=:0; Script kabum.py recebeu mais de 10 erros ao tentar download de pagina e foi abortado.")
		exit()

def mensagemPreco(titulo, valorAntigo, novoValor):
	if len(titulo) > 80:
		titulo = titulo[:80]

	os.system("export DISPLAY=:0; notify-send \"O preco abaixou!\" \" {} abaixou de R$ {} para R$ {}\"".format(titulo,valorAntigo,novoValor))

def barraProgresso(tempo):
	toolbar_width = 50
	tempo = tempo/50.0

	# setup toolbar
	sys.stdout.write("[%s]" % (" " * toolbar_width))
	sys.stdout.flush()
	sys.stdout.write("\b" * (toolbar_width+1)) # return to start of line, after '['

	for i in xrange(toolbar_width):
	    time.sleep(tempo) # do real work here
	    # update the bar
	    sys.stdout.write("-")
	    sys.stdout.flush()

	sys.stdout.write("]\n") # this ends the progress bar



def recebePagina(url): #recebe url e retorna pagina

	try:
		r = requests.get(url)	
		#r.raise_for_status()
		return r.text

	except requests.exceptions.RequestException as e:
		logging.error("recebePagina	: Erro ao receber pagina!", exc_info=True)
		print "Erro ao receber pagina: " + str(e)
		return e


def retornaListaDeProdutos(soup):
	index = 0
	while True:
		sair = False
		try:#tenta encontrar algum indice que seja valido
			listaComScripts = soup.findAll('script')#valores estao dentro de uma constante em um js
			script = listaComScripts[index] #escolhe o 19a script, ATENCAO! A LISTA DE SCRIPTS PODE MUDAR PARA OUTRA POSICAO
			m = re.search('listagemDados = \[(.*?)\]', script.encode('utf-8'))#usa regex para retirar porcao da constante com os valores
			listaProdutos = json.loads(m.group(0)[16:])#converte string para lista
			sair = True
		except:
			if index > len(listaComScripts):
				#logging.error("retornaListaDeProdutos	: Nenhum indice valido foi encontrado!", exc_info=True)
				print "Nenhum indice valido foi encontrado."
				return None
				exit()

			#print "Indice invalido, testando proximo."
			index += 1 #testa proximo indice
		
		if sair:
			return listaProdutos
			break

def retornaProdutosDaCategoria(url): #recebe categoria e retorna todas paginas

	listaDeProdutos = list()
	num_pagina = 1
	chegouAoFinal = False
	timeout = 5

	while not chegouAoFinal:

		endereco = url + "?pagina=" + str(num_pagina) + "&ordem=5&limite=100"

		#! tratar erro caso haja algum problema de rede, dns, acesso etc
		htmlDaPagina = recebePagina(endereco)

		soup = BeautifulSoup(htmlDaPagina, 'html.parser')
		produtosDaPagina = retornaListaDeProdutos(soup)

		if produtosDaPagina:

			for _ in produtosDaPagina:#adiciona os dicionarios na list
				listaDeProdutos.append(_)

			num_pagina += 1
			time.sleep(timeout)

		else:
			chegouAoFinal = True

	return listaDeProdutos


def recebeTodosProdutos(urls):
	"""
	Cria a pool e passa as urls
	"""

	futures_list = []
	results = []

	with ThreadPoolExecutor(max_workers=2) as executor:
		for url in urls:
			futures = executor.submit(retornaProdutosDaCategoria, url)
			futures_list.append(futures)

		#print "loop de futuros"
		
		for future in futures_list:
			try:
				result = future.result(timeout=60)
				results.append(result)
			except Exception as t:
				results.append(t)
	return results


def main():

	os.system("export DISPLAY=:0; notify-send -t 2500 \"Escaneando precos kabum\"")
	segundos = int(time.time())

	links = ("https://www.kabum.com.br/hardware/ssd-2-5",
			 "https://www.kabum.com.br/computadores/tablets/kindle",
			 "https://www.kabum.com.br/hardware/placa-de-video-vga/nvidia",
			 "https://www.kabum.com.br/hardware/disco-rigido-hd",
			 "https://www.kabum.com.br/celular-telefone/smartphones")

	links = ("https://www.kabum.com.br/eletronicos/calculadoras",
		 "https://www.kabum.com.br/computadores/tablets/kindle")

	hora=int(time.time())-10800#hora ja -3
	listaDadosParaDB = []
	listaDisponibilidade = []

	format = "%(asctime)s - %(levelname)s: %(message)s"
	DESTINO_LOG = './kabum.log'
	logging.basicConfig(format=format, level=logging.INFO,
                        datefmt="%d-%m %H:%M:%S", filename=DESTINO_LOG, filemode='a')
	logging.info("Main	: programa iniciado!")
	NOME_DB = "dbKabum.db"
	DB = DB_Kabum(NOME_DB)


	"""
	Passa links para pool receber todas paginas
	"""
	resultados = recebeTodosProdutos(links)



	for indice, resultado in enumerate(resultados):
		#print "Numero total de produtos na categoria: " + str(len(resultado))

		for _ in resultado:

			ident = _['codigo']
			titulo = _['nome']
			valor = _['preco_desconto']
			nome_fabricante = _['fabricante']['nome']
			cod_fabricante = _['fabricante']['codigo']
			disponibilidade = _['disponibilidade'] #boolean
			is_openbox = _['is_openbox'] #boolean
			tem_frete_gratis = _['tem_frete_gratis'] #boolean
			link = links[indice]
			#is_marketplace = _['is_marketplace']

			pesquisa = DB.procuraProduto(ident)#procura se produto ja existe no banco de dados

			if len(pesquisa) == 0:#se o prod nao existir preenche o banco de dados com o novo produto
				
				DB.preencheDB(ident, titulo, nome_fabricante, cod_fabricante, disponibilidade, 
					is_openbox,tem_frete_gratis,link)
				listaDadosParaDB.append([hora, valor, ident])#armazena valores em lista temporaria
			
			else:

				listaDadosParaDB.append([hora, valor, ident])#adiciona valores em lista temporaria
				if disponibilidade != pesquisa[0][4]: #se a disponibilidade mudou
					listaDisponibilidade.append([ident, disponibilidade])

		DB.preencheValoresDB(listaDadosParaDB)#ao final da categoria, passa lista de dados para funcao salvar no banco
		listaDadosParaDB = []#limpa lista

		if listaDisponibilidade:
			DB.preencheDisponibilidade(listaDisponibilidade)
			listaDisponibilidade = []


	logging.info("Main	: programa terminado!")
	tempo_exec = (int(time.time()) - segundos)/60
	os.system("export DISPLAY=:0; notify-send -t 10000 \"Script kabum.py executado com SUCESSO. {}m\"".
		format(tempo_exec))


if __name__ == '__main__':
    main()
