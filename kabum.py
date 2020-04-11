#!/usr/bin/env python

import requests
from bs4 import BeautifulSoup
import time
import sqlite3
import os
import sys


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
delay = 15 #tempo minimo entre requisicoes, em segs
cont_erros = 0
hora=int(time.time())-10800#hora ja -3
listaDadosParaDB = []


while True:

	#link = "https://www.kabum.com.br/hardware/disco-rigido-hd?ordem=5&limite=100&pagina=" 
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

	section = soup.findAll("section", {"class": "listagem-box"})

	#print section[0]

	if len(section) == 0:#caso tenha chegado ao final da pagina, passa para proxima categoria
		num = 1

		if num_lista+1 <= len(links)-1: 
			num_lista += 1
			link = links[num_lista] + str(num) + "&ordem=5&limite=100"
			print "tira " + link

		else:
			num_lista = 0
			link = links[num_lista] + str(num) + "&ordem=5&limite=100"
			print "Final? Dormindo minutos.: " + str((300*delay)/60)
			exit()
			barraProgresso(300*delay)
			hora=int(time.time())-10800#hora ja -3	

		while True:
			r = requests.get(link)
			if r.status_code != 200:
				print "Erro ao receber pagina: " + str(r.status_code)
				cont_erros += 1
				mensagemErro(cont_erros)
				barraProgresso(500)
			else:
				print "	Proxima categoria recebida"
				break


		soup = BeautifulSoup(r.text, 'html.parser')
		section = soup.findAll("section", {"class": "listagem-box"})

	for _ in range(len(section)):

		b = BeautifulSoup(str(section[_]), 'html.parser')
		ident = b.findAll('a', href=True)[1]['data-id']
		titulo = section[_].findAll("a")
		titulo = titulo[1].text

		valor = section[_].findAll("div", {"class": "listagem-preco"})

		if len(valor) != 0: 
			valor = valor[0].text 
			valor = int(valor[3:-3].replace('.',''))
		else: 
			valor = section[0].findAll("div", {"class": "listagem-precoavista"})
			
			if len(valor) == 0:
				valor = 666
			else:
				valor = valor[0].text
				valor = int(valor[3:-3].replace('.',''))

		resultado = procuraProduto(ident)

		if len(resultado) == 0:#preenche o banco de dados
			preencheDB(ident, titulo, valor, valor)
			#preencheValoresDB(hora, valor, ident)
			listaDadosParaDB.append([hora, valor, ident])#armazena valores em lista temporaria
		else:
			#preencheValoresDB(hora, valor, ident)
			listaDadosParaDB.append([hora, valor, ident])#adiciona valores em lista temporaria
	
	preencheValoresDB(listaDadosParaDB)#ao final da pagina, passa lista de dados para funcao salvar no banco
	listaDadosParaDB = []#limpa lista
	print "Dormindo " + "pag. " + str(num) + " [ " + links[num_lista][24:] + " ]"
	barraProgresso(delay)
	num = num + 1
