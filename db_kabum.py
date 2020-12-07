import sqlite3
import time

class DB_Kabum:

	def __init__(self, NOME_DB):
		self.NOME_DB = NOME_DB
		self.conn = sqlite3.connect(self.NOME_DB)
		self.criaTabelas()

	def criaTabelas(self):

		self.conn.execute("""
		CREATE TABLE IF NOT EXISTS produto (
			idProduto	INTEGER,
			titulo	VARCHAR(500),
			fabricante	VARCHAR(500),
			cod_fabricante	INTEGER,
			disponivel	BOOLEAN,
			openbox	BOOLEAN,
			freteGratis	BOOLEAN,
			link	VARCHAR(700),
			media_6_meses	REAL,
			media_3_meses	REAL,
			media_1_mes	REAL,
			valor_atual	REAL,
			PRIMARY KEY(idProduto)
				)
			""")

		self.conn.execute("""
			CREATE TABLE IF NOT EXISTS precoProduto (
			dataUNIX INTEGER,  
			valor INTEGER, 
			idProduto   INTEGER NOT NULL,  
			FOREIGN KEY (idProduto)  REFERENCES produto (idProduto)
				)
			""")

		self.conn.commit()


	def procuraProduto(self, idProduto):
		
		resultado = self.conn.execute("SELECT * FROM produto WHERE idProduto = \"%s\"" %idProduto).fetchall()
		return resultado

	def preencheDB(self, ident, titulo, nome_fabricante, cod_fabricante, disponibilidade, 
						is_openbox,tem_frete_gratis,link):
		tup=(ident, titulo, nome_fabricante, cod_fabricante, disponibilidade, 
						is_openbox,tem_frete_gratis,link)
		dados=[]
		dados.append(tup)
		self.conn.execute("PRAGMA foreign_keys = 1")
		self.conn.executemany('''INSERT INTO produto (idProduto, titulo, fabricante, cod_fabricante, disponivel, openbox, freteGratis, link) 
			VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', dados)
		self.conn.commit()

	def preencheValoresDB(self, listaComValores):
		
		self.conn.execute("PRAGMA foreign_keys = 1")

		for prod in listaComValores:

			tup=(prod[0], prod[1], prod[2])
			dados=[]
			dados.append(tup)

			try:
				self.conn.executemany('''INSERT INTO precoProduto (dataUNIX, valor, idProduto) VALUES (?, ?, ?)''', dados)
			except sqlite3.Error as e:
				print("An error occurred:", e.args[0])
				logging.error("preencheValoresDB	: Ocorreu um erro.", exc_info=True)


		self.conn.commit()

	def preencheDisponibilidade(self, listaDisponibilidade):

		self.conn.execute("PRAGMA foreign_keys = 1")

		for prod in listaDisponibilidade:
			tup = (prod[1], prod[0])
			dados=[]
			dados.append(tup)

			try:
				self.conn.executemany('''UPDATE produto SET disponivel = ? WHERE idProduto = ?''', dados)
			except sqlite3.Error as e:
				print("An error occurred:", e.args[0])
				logging.error("preencheDisponibilidade	: Ocorreu um erro.", exc_info=True)

		self.conn.commit()


	def atualizaPrecos(self, ultimoMes=False, tresMeses=False, seisMeses=False, precoAtual=False):

		a = self.conn.execute("SELECT idProduto FROM produto WHERE disponivel = 1").fetchall()
		lista_ids = []

		for _ in a:
			lista_ids.append(_[0])

		inicio = time.time()

		for produto in lista_ids:

			if seisMeses:
			#media dos ultimos 6 meses
				data = time.time() - 60*60*24*30*6
				media= self.conn.execute("SELECT round(avg(valor),2) FROM precoProduto where idProduto = ? and dataUNIX >= ?", 
					(produto, data)).fetchall()[0][0]
				self.conn.execute("UPDATE produto SET media_6_meses = ? WHERE idProduto = ?", (media, produto))

			if tresMeses:
			#media dos ultimos 3 meses
				data = time.time() - 60*60*24*30*3
				media = self.conn.execute("SELECT round(avg(valor),2) FROM precoProduto where idProduto = ? and dataUNIX >= ?", 
					(produto, data)).fetchall()[0][0]
				self.conn.execute("UPDATE produto SET media_3_meses = ? WHERE idProduto = ?", (media, produto))

			if ultimoMes:
			#media do ultimo mes
				data = time.time() - 60*60*24*30*1
				media = self.conn.execute("SELECT round(avg(valor),2) FROM precoProduto where idProduto = ? and dataUNIX >= ?", 
					(produto, data)).fetchall()[0][0]
				self.conn.execute("UPDATE produto SET media_1_mes = ? WHERE idProduto = ?", (media, produto))

			if precoAtual:
			#ultimo valor no db
				ultima_data = self.conn.execute("SELECT max(dataUNIX) FROM precoProduto where idProduto = ?",
					(produto,)).fetchall()[0][0]

				valor = self.conn.execute("SELECT valor FROM precoProduto where idProduto = ? AND dataUNIX= ?",
					(produto, ultima_data)).fetchall()[0][0]
				self.conn.execute("UPDATE produto SET valor_atual = ? WHERE idProduto = ?", (valor, produto))

		self.conn.commit()
