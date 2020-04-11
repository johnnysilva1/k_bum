#!/usr/bin/env python

import requests
from bs4 import BeautifulSoup
import time
import sqlite3
import os
import sys
import json
import re


#CREATE TABLE precoProduto (dataUNIX INTEGER,  valor INTEGER, idProduto   INTEGER NOT NULL,  FOREIGN KEY (idProduto)  REFERENCES produto (idProduto));

#'INSERT INTO precoProduto (dataUNIX, valor, idProduto) VALUES (84108, 84108,84108);

#create table produto (idProduto INTEGER PRIMARY KEY,  titulo VARCHAR(500), maiorValor  INTEGER, menorValor INTEGER);
#INSERT INTO produto (id, idProduto, titulo, maiorValor, menorValor) VALUES ("POST1", "ZEBUNDA", 50, 10, 0.4, "noticia", "pernambuco", 211215444, "G1", "ze das couves mata traficante");
#select * from produto WHERE maiorValor != menorValor;

#conn=sqlite3.connect("clientdatabase.db")
#conn.execute("PRAGMA foreign_keys = 1")//LIBERA PRAGMA
#cur=conn.cursor()

#UPDATE produto SET maiorValor = (SELECT MAX(valor) FROM precoProduto WHERE precoProduto.idProduto = produto.idProduto);

#INSERT INTO NOVOproduto (idProduto, titulo,  maiorValor, menorValor)  SELECT idProduto, titulo, maiorValor, menorValor FROM produto;



def procuraProduto(idProduto):
	con = sqlite3.connect('dbKabum.db')
	c = con.cursor()
	c.execute("SELECT * FROM produto WHERE idProduto = \"%s\"" %idProduto)
	resultado = c.fetchall()
	con.close()
	return resultado

def preencheDB(idProduto, titulo, valorAntigo, novoValor):
	tup=(idProduto, titulo, valorAntigo, novoValor)
	dados=[]
	dados.append(tup)
	con = sqlite3.connect('dbKabum.db')
	con.execute("PRAGMA foreign_keys = 1")
	c = con.cursor()
	c.executemany('''INSERT INTO produto (idProduto, titulo, maiorValor, menorValor) VALUES (?, ?, ?, ?)''', dados)
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

	con.commit()
	con.close()


def mensagemErro(qtdErros):
	if (qtdErros) >= 10:
		os.system("Script kabum.py recebeu mais de 10 erros ao tentar download de pagina")

def mensagemPreco(titulo, valorAntigo, novoValor):
	if len(titulo) > 80:
		titulo = titulo[:80]

	os.system("notify-send \"O preco abaixou!\" \" {} abaixou de R$ {} para R$ {}\"".format(titulo,valorAntigo,novoValor))

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



links = ("https://www.kabum.com.br/hardware/ssd-2-5?pagina=",
		 "https://www.kabum.com.br/computadores/tablets/kindle?pagina=",
		 "https://www.kabum.com.br/hardware/placa-de-video-vga/nvidia?pagina=",
		 "https://www.kabum.com.br/hardware/disco-rigido-hd?ordem=5&limite=100&pagina=",
		 "https://www.kabum.com.br/celular-telefone/smartphones?pagina=")#lembrar de por a ?pagina= ao final do nome
num = 1 #1
num_lista = 0 #0
delay = 30 #tempo minimo entre requisicoes, em segs
cont_erros = 0
hora=int(time.time())-10800#hora ja -3
listaDadosParaDB = []


while True:

	#link = "https://www.kabum.com.br/hardware/disco-rigido-hd?ordem=5&limite=100&pagina=" 

	if num_lista > len(links)-1:#se chegou ao final da lista de links termina programa 
		exit()


	link = links[num_lista] + str(num) + "&ordem=5&limite=100"

	while True:
		r = requests.get(link)
		if r.status_code != 200:
			print "Erro ao receber pagina: " + str(r.status_code)
			cont_erros += 1
			mensagemErro(cont_erros)
			barraProgresso(500)
		else: 
			break


	soup = BeautifulSoup(r.text, 'html.parser')
	listaComScripts = soup.findAll('script')#valores estao dentro de uma constante em um js
	script = listaComScripts[19] #escolhe o 19a script
	m = re.search('listagemDados = \[(.*?)\]', script.encode('utf-8'))#usa regex para retirar porcao da constante com os valores
	listaProdutos = json.loads(m.group(0)[16:])#converte string para lista

	# #listaProdutos.keys()
	# avaliacao_nota
	# disponibilidade
	# is_openbox
	# preco_desconto
	# preco
	# alt
	# img
	# nome
	# link_descricao
	# menu
	# oferta
	# preco_prime
	# tem_frete_gratis
	# brinde
	# preco_antigo
	# fabricante
	# is_marketplace
	# frete_gratis_somente_prime
	# botao_marketplace
	# preco_desconto_prime
	# codigo
	# avaliacao_numero

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

	#avaliacao_nota, disponibilidade, is_openbox, preco_desconto, preco, alt, img, nome, link_descricao, menu, oferta, preco_prime, 
	#tem_frete_gratis, brinde, preco_antigo, fabricante, is_marketplace, frete_gratis_somente_prime, botao_marketplace, preco_desconto_prime, codigo, avaliacao_numero,
	#print section[0]

	
	if listaProdutos:
		for _ in listaProdutos:

			ident = _['codigo']
			titulo = _['nome']
			valor = _['preco_desconto']

			resultado = procuraProduto(ident)#procura se produto ja existe no banco de dados

			if len(resultado) == 0:#preenche o banco de dados com o novo produto
				preencheDB(ident, titulo, valor, valor)
				listaDadosParaDB.append([hora, valor, ident])#armazena valores em lista temporaria
			else:
				listaDadosParaDB.append([hora, valor, ident])#adiciona valores em lista temporaria


		preencheValoresDB(listaDadosParaDB)#ao final da pagina, passa lista de dados para funcao salvar no banco
		listaDadosParaDB = []#limpa lista
		print "Dormindo " + "pag. " + str(num) + " [ " + links[num_lista][24:] + " ]"
		barraProgresso(delay)
		num = num + 1		

	else:
		num = 1
		num_lista = num_lista + 1

		
	
	
