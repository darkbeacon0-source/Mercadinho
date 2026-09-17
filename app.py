from flask import Flask, request, redirect, render_template_string
import sqlite3
from datetime import date
import os

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE_DIR, 'mercadinho.db')

def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    con = db()
    con.executescript('''
    CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT UNIQUE,
        nome TEXT NOT NULL,
        categoria TEXT,
        custo REAL NOT NULL DEFAULT 0,
        venda REAL NOT NULL DEFAULT 0,
        quantidade INTEGER NOT NULL DEFAULT 0,
        estoque_minimo INTEGER NOT NULL DEFAULT 0,
        validade TEXT,
        fornecedor TEXT
    );
    CREATE TABLE IF NOT EXISTS vendas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT NOT NULL,
        total REAL NOT NULL,
        pagamento TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS itens_venda (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        venda_id INTEGER NOT NULL,
        produto_id INTEGER NOT NULL,
        quantidade INTEGER NOT NULL,
        preco REAL NOT NULL
    );
    CREATE TABLE IF NOT EXISTS movimentacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        produto_id INTEGER NOT NULL,
        tipo TEXT NOT NULL,
        quantidade INTEGER NOT NULL,
        data TEXT NOT NULL,
        observacao TEXT
    );
    ''')
    con.commit(); con.close()

STYLE='''<style>body{font-family:Arial;margin:0;background:#f4f6f8;color:#222}nav{background:#20242a;padding:16px}nav a{color:white;margin-right:20px;text-decoration:none;font-weight:bold}.wrap{max-width:1100px;margin:30px auto;padding:0 15px}.cards{display:flex;gap:15px;flex-wrap:wrap}.card{background:white;padding:20px;border-radius:10px;box-shadow:0 2px 8px #ddd;min-width:180px}table{width:100%;border-collapse:collapse;background:white}th,td{padding:10px;border-bottom:1px solid #ddd;text-align:left}input,select{padding:9px;margin:4px;width:95%;box-sizing:border-box}button,.btn{background:#2563eb;color:white;border:0;padding:10px 14px;border-radius:6px;text-decoration:none;cursor:pointer}.danger{background:#dc2626}.warn{color:#b45309}.ok{color:#15803d}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px}</style>'''
BASE='''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Mercadinho</title>'''+STYLE+'''</head><body><nav><a href="/">Dashboard</a><a href="/produtos">Produtos</a><a href="/estoque">Estoque</a><a href="/venda">Nova venda</a><a href="/vendas">Vendas</a><a href="/validade">Validades</a></nav><div class="wrap">{{content|safe}}</div></body></html>'''
def page(content): return render_template_string(BASE,content=content)

@app.route('/')
def home():
    con=db(); hoje=date.today().isoformat()
    total=con.execute("SELECT COALESCE(SUM(total),0) x FROM vendas WHERE date(data)=?",(hoje,)).fetchone()['x']
    vendas=con.execute("SELECT COUNT(*) x FROM vendas WHERE date(data)=?",(hoje,)).fetchone()['x']
    produtos=con.execute("SELECT COUNT(*) x FROM produtos").fetchone()['x']
    baixo=con.execute("SELECT COUNT(*) x FROM produtos WHERE quantidade<=estoque_minimo").fetchone()['x']
    con.close()
    return page(f'''<h1>Dashboard</h1><div class="cards"><div class="card"><b>Vendas hoje</b><h2>R$ {total:.2f}</h2></div><div class="card"><b>Nº de vendas</b><h2>{vendas}</h2></div><div class="card"><b>Produtos</b><h2>{produtos}</h2></div><div class="card"><b>Estoque baixo</b><h2>{baixo}</h2></div></div>''')

@app.route('/produtos')
def produtos():
    con=db(); rows=con.execute('SELECT * FROM produtos ORDER BY nome').fetchall(); con.close()
    trs=''.join(f'''<tr><td>{r['codigo'] or '-'}</td><td>{r['nome']}</td><td>{r['quantidade']}</td><td>R$ {r['venda']:.2f}</td><td>{r['validade'] or '-'}</td><td><a class="btn" href="/produto/editar/{r['id']}">Editar</a> <a class="btn danger" href="/produto/excluir/{r['id']}" onclick="return confirm('Excluir produto?')">Excluir</a></td></tr>''' for r in rows)
    return page(f'''<h1>Produtos</h1><a class="btn" href="/produto/novo">+ Cadastrar produto</a><br><br><table><tr><th>Código</th><th>Nome</th><th>Qtd.</th><th>Venda</th><th>Validade</th><th>Ações</th></tr>{trs}</table>''')

FORM='''<h1>{titulo}</h1><form method="post"><div class="grid"><label>Código de barras<input name="codigo" value="{codigo}"></label><label>Nome *<input name="nome" required value="{nome}"></label><label>Categoria<input name="categoria" value="{categoria}"></label><label>Preço de custo<input type="number" step="0.01" name="custo" value="{custo}"></label><label>Preço de venda<input type="number" step="0.01" name="venda" value="{venda}"></label><label>Quantidade<input type="number" name="quantidade" min="0" value="{quantidade}"></label><label>Estoque mínimo<input type="number" name="estoque_minimo" min="0" value="{minimo}"></label><label>Validade<input type="date" name="validade" value="{validade}"></label><label>Fornecedor<input name="fornecedor" value="{fornecedor}"></label></div><button>Salvar</button></form>'''
def form_values(r=None):
    r=r or {}; return FORM.format(titulo='Editar produto' if r else 'Novo produto',codigo=r.get('codigo',''),nome=r.get('nome',''),categoria=r.get('categoria',''),custo=r.get('custo',0),venda=r.get('venda',0),quantidade=r.get('quantidade',0),minimo=r.get('estoque_minimo',0),validade=r.get('validade','') or '',fornecedor=r.get('fornecedor',''))

@app.route('/produto/novo',methods=['GET','POST'])
def novo():
    if request.method=='POST':
        f=request.form; con=db(); con.execute('INSERT INTO produtos(codigo,nome,categoria,custo,venda,quantidade,estoque_minimo,validade,fornecedor) VALUES(?,?,?,?,?,?,?,?,?)',(f['codigo'] or None,f['nome'],f['categoria'],float(f['custo'] or 0),float(f['venda'] or 0),int(f['quantidade'] or 0),int(f['estoque_minimo'] or 0),f['validade'] or None,f['fornecedor'])); con.commit(); con.close(); return redirect('/produtos')
    return page(form_values())

@app.route('/produto/editar/<int:id>',methods=['GET','POST'])
def editar(id):
    con=db(); r=con.execute('SELECT * FROM produtos WHERE id=?',(id,)).fetchone()
    if request.method=='POST':
        f=request.form; con.execute('UPDATE produtos SET codigo=?,nome=?,categoria=?,custo=?,venda=?,quantidade=?,estoque_minimo=?,validade=?,fornecedor=? WHERE id=?',(f['codigo'] or None,f['nome'],f['categoria'],float(f['custo'] or 0),float(f['venda'] or 0),int(f['quantidade'] or 0),int(f['estoque_minimo'] or 0),f['validade'] or None,f['fornecedor'],id)); con.commit(); con.close(); return redirect('/produtos')
    con.close(); return page(form_values(dict(r)))

@app.route('/produto/excluir/<int:id>')
def excluir(id):
    con=db(); con.execute('DELETE FROM produtos WHERE id=?',(id,)); con.commit(); con.close(); return redirect('/produtos')

@app.route('/estoque')
def estoque():
    con=db(); rows=con.execute('SELECT * FROM produtos ORDER BY quantidade,nome').fetchall(); con.close(); trs=''.join(f"<tr><td>{r['nome']}</td><td>{r['quantidade']}</td><td>{r['estoque_minimo']}</td><td class='{('warn' if r['quantidade']<=r['estoque_minimo'] else 'ok')}'>{'BAIXO' if r['quantidade']<=r['estoque_minimo'] else 'OK'}</td></tr>" for r in rows); return page(f'<h1>Controle de estoque</h1><table><tr><th>Produto</th><th>Quantidade</th><th>Mínimo</th><th>Status</th></tr>{trs}</table>')

@app.route('/venda',methods=['GET','POST'])
def venda():
    con=db()
    if request.method=='POST':
        pid=int(request.form['produto_id']); qtd=int(request.form['quantidade']); pagamento=request.form['pagamento']; p=con.execute('SELECT * FROM produtos WHERE id=?',(pid,)).fetchone()
        if not p or qtd<=0 or qtd>p['quantidade']: con.close(); return page('<h2>Quantidade inválida ou estoque insuficiente.</h2><a href="/venda">Voltar</a>')
        total=p['venda']*qtd; cur=con.execute('INSERT INTO vendas(data,total,pagamento) VALUES(datetime(\'now\',\'localtime\'),?,?)',(total,pagamento)); vid=cur.lastrowid; con.execute('INSERT INTO itens_venda(venda_id,produto_id,quantidade,preco) VALUES(?,?,?,?)',(vid,pid,qtd,p['venda'])); con.execute('UPDATE produtos SET quantidade=quantidade-? WHERE id=?',(qtd,pid)); con.execute('INSERT INTO movimentacoes(produto_id,tipo,quantidade,data,observacao) VALUES(?,\'VENDA\',?,datetime(\'now\',\'localtime\'),?)',(pid,qtd,f'Venda #{vid}')); con.commit(); con.close(); return redirect('/vendas')
    rows=con.execute('SELECT * FROM produtos WHERE quantidade>0 ORDER BY nome').fetchall(); con.close(); opts=''.join(f'<option value="{r["id"]}">{r["nome"]} — R$ {r["venda"]:.2f} (estoque: {r["quantidade"]})</option>' for r in rows); return page(f'''<h1>Nova venda</h1><form method="post"><label>Produto<select name="produto_id" required>{opts}</select></label><label>Quantidade<input type="number" name="quantidade" min="1" required></label><label>Pagamento<select name="pagamento"><option>Dinheiro</option><option>Pix</option><option>Débito</option><option>Crédito</option></select></label><button>Registrar venda</button></form>''')

@app.route('/vendas')
def vendas():
    con=db(); rows=con.execute('SELECT * FROM vendas ORDER BY id DESC').fetchall(); con.close(); trs=''.join(f"<tr><td>#{r['id']}</td><td>{r['data']}</td><td>R$ {r['total']:.2f}</td><td>{r['pagamento']}</td></tr>" for r in rows); return page(f'<h1>Vendas</h1><table><tr><th>ID</th><th>Data</th><th>Total</th><th>Pagamento</th></tr>{trs}</table>')

@app.route('/validade')
def validade():
    con=db(); rows=con.execute("SELECT * FROM produtos WHERE validade IS NOT NULL ORDER BY validade").fetchall(); con.close(); hoje=date.today().isoformat(); trs=''.join(f"<tr><td>{r['nome']}</td><td>{r['quantidade']}</td><td>{r['validade']}</td><td class='{('warn' if r['validade']<=hoje else 'ok')}'>{'VENCIDO' if r['validade']<hoje else ('VENCE HOJE' if r['validade']==hoje else 'ATIVO')}</td></tr>" for r in rows); return page(f'<h1>Controle de validade</h1><table><tr><th>Produto</th><th>Qtd.</th><th>Validade</th><th>Status</th></tr>{trs}</table>')

init_db()
if __name__=='__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
