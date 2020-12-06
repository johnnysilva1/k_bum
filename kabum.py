#!/usr/bin/env python

import requests
from bs4 import BeautifulSoup
import time
import sqlite3
import os
import sys
import json
import re
import logging


def procuraProduto(idProduto):
	con = sqlite3.connect('dbKabum.db')
	c = con.cursor()
	c.execute("SELECT * FROM produto WHERE idProduto = \"%s\"" %idProduto)
	resultado = c.fetchall()
	con.close()
	return resultado

def preencheDB(ident, titulo, nome_fabricante, cod_fabricante, disponibilidade, 
					is_openbox,tem_frete_gratis,link):
	tup=(ident, titulo, nome_fabricante, cod_fabricante, disponibilidade, 
					is_openbox,tem_frete_gratis,link)
	dados=[]
	dados.append(tup)
	con = sqlite3.connect('dbKabum.db')
	con.execute("PRAGMA foreign_keys = 1")
	c = con.cursor()
	c.executemany('''INSERT INTO produto (idProduto, titulo, fabricante, cod_fabricante, disponivel, openbox, freteGratis, link) 
		VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', dados)
	con.commit()
	con.close()

def preencheValoresDB(listaComValores):
	
	con = sqlite3.connect('dbKabum.db')
	con.execute("PRAGMA foreign_keys = 1")
	c = con.cursor()

	for prod in listaComValores:

		tup=(prod[0], prod[1], prod[2])
		dados=[]
		dados.append(tup)

		try:
			c.executemany('''INSERT INTO precoProduto (dataUNIX, valor, idProduto) VALUES (?, ?, ?)''', dados)
		except sqlite3.Error as e:
			print("An error occurred:", e.args[0])
			logging.error("preencheValoresDB	: Ocorreu um erro.", exc_info=True)


	con.commit()
	con.close()

def preencheDisponibilidade(listaDisponibilidade):

	con = sqlite3.connect('dbKabum.db')
	con.execute("PRAGMA foreign_keys = 1")
	c = con.cursor()

	for prod in listaDisponibilidade:
		tup = (prod[1], prod[0])
		dados=[]
		dados.append(tup)

		try:
			c.executemany('''UPDATE produto SET disponivel = ? WHERE idProduto = ?''', dados)
		except sqlite3.Error as e:
			print("An error occurred:", e.args[0])
			logging.error("preencheDisponibilidade	: Ocorreu um erro.", exc_info=True)

	con.commit()
	con.close()


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


def recebePagina(link):
	while True:
		r = None
		try:
			r = requests.get(link)
			return r

		except:
			if r.status_code != 200:
				print "Erro ao receber pagina: " + str(r.status_code)
				logging.error("recebePagina	: Erro ao receber pagina!", exc_info=True)
				cont_erros += 1
				mensagemErro(cont_erros)
				barraProgresso(500)
			else:
				logging.error("recebePagina	: Erro catastrofico ao receber pagina!", exc_info=True)
				print "Erro catastrofico ao receber pagina: " + str(r.status_code)
				cont_erros += 1
				mensagemErro(cont_erros)
				barraProgresso(500)

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
				logging.error("retornaListaDeProdutos	: Nenhum indice valido foi encontrado!", exc_info=True)
				print "Nenhum indice valido foi encontrado."
				exit()

			#print "Indice invalido, testando proximo."
			index += 1 #testa proximo indice
		
		if sair:
			return listaProdutos
			break


def atualizaPrecos():
	con = sqlite3.connect('dbKabum.db')
	c = con.cursor()
	c.execute("SELECT idProduto FROM produto WHERE disponivel = 1")
	a = c.fetchall()
	lista_ids = []

	for _ in a:
		lista_ids.append(_[0])

	inicio = time.time()

	for produto in lista_ids:

		#media dos ultimos 6 meses
		# data = time.time() - 60*60*24*30*6
		# c.execute("select round(avg(valor),2) FROM precoProduto where idProduto = ? and dataUNIX >= ?", (produto, data))
		# media = c.fetchall()[0][0]
		# c.execute("UPDATE produto SET media_6_meses = ? WHERE idProduto = ?", (media, produto))

		#media dos ultimos 3 meses
		# data = time.time() - 60*60*24*30*3
		# c.execute("select round(avg(valor),2) FROM precoProduto where idProduto = ? and dataUNIX >= ?", (produto, data))
		# media = c.fetchall()[0][0]
		# c.execute("UPDATE produto SET media_3_meses = ? WHERE idProduto = ?", (media, produto))

		#media do ultimo mes
		# data = time.time() - 60*60*24*30*1
		# c.execute("select round(avg(valor),2) FROM precoProduto where idProduto = ? and dataUNIX >= ?", (produto, data))
		# media = c.fetchall()[0][0]
		# c.execute("UPDATE produto SET media_1_mes = ? WHERE idProduto = ?", (media, produto))

		#ultimo valor no db
		c.execute("select max(dataUNIX) FROM precoProduto where idProduto = ?", (produto,))
		ultima_data = c.fetchall()[0][0]
		c.execute("select valor FROM precoProduto where idProduto = ? AND dataUNIX= ?", (produto, ultima_data))
		valor = c.fetchall()[0][0]

		c.execute("UPDATE produto SET valor_atual = ? WHERE idProduto = ?", (valor, produto))

	con.commit()
	con.close()


def main():

	segundos = int(time.time())

	links = ("https://www.kabum.com.br/hardware/ssd-2-5?pagina=",
			 "https://www.kabum.com.br/computadores/tablets/kindle?pagina=",
			 "https://www.kabum.com.br/hardware/placa-de-video-vga/nvidia?pagina=",
			 "https://www.kabum.com.br/hardware/disco-rigido-hd?ordem=5&limite=100&pagina=",
			 "https://www.kabum.com.br/celular-telefone/smartphones?pagina=")#lembrar de por a ?pagina= ao final do nome
	num = 1 #1
	num_lista = 0 #0
	delay = 5 #tempo minimo entre requisicoes, em segs
	cont_erros = 0
	hora=int(time.time())-10800#hora ja -3
	listaDadosParaDB = []
	listaDisponibilidade = []


	format = "%(asctime)s - %(levelname)s: %(message)s"
	logging.basicConfig(format=format, level=logging.INFO,
                        datefmt="%H:%M:%S", filename='/home/johnny/Desktop/Arquivos/kabum.log', filemode='a')

	os.system("export DISPLAY=:0; notify-send -t 2500 \"Escaneando precos kabum\"")
	logging.info("Main	: programa iniciado!")

	while True:

		#link = "https://www.kabum.com.br/hardware/disco-rigido-hd?ordem=5&limite=100&pagina=" 

		if num_lista > len(links)-1:#se chegou ao final da lista de links termina programa 
			#atualizaPrecos()
			logging.info("Main	: programa terminado!")
			tempo_exec = (int(time.time()) - segundos)/60
			os.system("export DISPLAY=:0; notify-send -t 10000 \"Script kabum.py executado com SUCESSO. {}m\"".
				format(tempo_exec))
			exit()


		link = links[num_lista] + str(num) + "&ordem=5&limite=100"

		pagina = recebePagina(link)
		soup = BeautifulSoup(pagina.text, 'html.parser')
		listaProdutos = retornaListaDeProdutos(soup)

		
		if listaProdutos:
			for _ in listaProdutos:

				ident = _['codigo']
				titulo = _['nome']
				valor = _['preco_desconto']
				nome_fabricante = _['fabricante']['nome']
				cod_fabricante = _['fabricante']['codigo']
				disponibilidade = _['disponibilidade'] #boolean
				is_openbox = _['is_openbox'] #boolean
				tem_frete_gratis = _['tem_frete_gratis'] #boolean
				#is_marketplace = _['is_marketplace']

				resultado = procuraProduto(ident)#procura se produto ja existe no banco de dados

				if len(resultado) == 0:#preenche o banco de dados com o novo produto
					preencheDB(ident, titulo, nome_fabricante, cod_fabricante, disponibilidade, 
						is_openbox,tem_frete_gratis,link)
					listaDadosParaDB.append([hora, valor, ident])#armazena valores em lista temporaria
				else:
					listaDadosParaDB.append([hora, valor, ident])#adiciona valores em lista temporaria
					if disponibilidade != resultado[0][4]: #se a disponibilidade mudou
						listaDisponibilidade.append([ident, disponibilidade])

			preencheValoresDB(listaDadosParaDB)#ao final da pagina, passa lista de dados para funcao salvar no banco
			listaDadosParaDB = []#limpa lista

			if listaDisponibilidade:
				preencheDisponibilidade(listaDisponibilidade)
				listaDisponibilidade = []

			logging.info("Main	: dormindo (pagina recebida: %s)",links[num_lista][24:])

			print "Dormindo " + "pag. " + str(num) + " [ " + links[num_lista][24:] + " ]"
			barraProgresso(delay)
			num = num + 1		

		else:
			num = 1
			num_lista = num_lista + 1

if __name__ == '__main__':
    main()

	# avaliacao_nota = _['avaliacao_nota']
	# disponibilidade = _['disponibilidade']
	# is_openbox = _['is_openbox']
	# preco_desconto = _['preco_desconto']
	# preco = _['preco']
	# alt = _['alt']
	# img = _['img']
	# nome = _['nome']
	# link_descricao = _['link_descricao']
	# menu = _['menu']
	# oferta = _['oferta']
	# preco_prime = _['preco_prime']
	# tem_frete_gratis = _['tem_frete_gratis']
	# brinde = _['brinde']
	# preco_antigo = _['preco_antigo']
	# fabricante = _['fabricante']
	# is_marketplace = _['is_marketplace']
	# frete_gratis_somente_prime = _['frete_gratis_somente_prime']
	# botao_marketplace = _['botao_marketplace']
	# preco_desconto_prime = _['preco_desconto_prime']
	# codigo = _['codigo']
	# avaliacao_numero = _['avaliacao_numero']

	#avaliacao_nota, disponibilidade, is_openbox, preco_desconto, preco, alt, img, nome, link_descricao, menu, oferta, preco_prime,tem_frete_gratis, brinde, preco_antigo, fabricante, is_marketplace, frete_gratis_somente_prime, botao_marketplace, preco_desconto_prime, codigo, avaliacao_numero,
	#print section[0]

	#CREATE TABLE produto (idProduto INTEGER PRIMARY KEY,  titulo VARCHAR(500), fabricante  VARCHAR(500), cod_fabricante INTEGER, disponivel BOOLEAN, openbox BOOLEAN, freteGratis BOOLEAN, link VARCHAR(700))
	#retorna o id, titulo e precomedio de todos produtos
	#select d.idProduto, d.titulo, avg(e.valor) FROM precoProduto e, produto d where e.idProduto = d.idProduto AND d.disponivel = 1 group by d.titulo;

	# CREATE TABLE "produto" (
	# `idProduto`	INTEGER,
	# `titulo`	VARCHAR(500),
	# `fabricante`	VARCHAR(500),
	# `cod_fabricante`	INTEGER,
	# `disponivel`	BOOLEAN,
	# `openbox`	BOOLEAN,
	# `freteGratis`	BOOLEAN,
	# `link`	VARCHAR(700),
	# `media_6_meses`	REAL,
	# `media_3_meses`	REAL,
	# `media_1_mes`	REAL,
	# `valor_atual`	REAL,
	# PRIMARY KEY(idProduto)
	# )