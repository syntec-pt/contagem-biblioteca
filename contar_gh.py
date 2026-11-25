"""Contagem da Biblioteca de Anúncios num runner do GitHub Actions (24/11/2026): cada execução sai por um IP novo.
Uso: python3 contar_gh.py <lote.json> <k> <n> <saida.jsonl>. A função contar() é cópia literal de x2311/meta/meta_lib.py.
Controlo com a página da Syntec no início e a cada 25: se falhar, apaga os zeros desde o último controlo bom e para (o resto fica para outra execução)."""
import json, re, sys, time
from playwright.sync_api import sync_playwright
POS = "1399253189940293"
URL = "https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country=ALL&is_targeted_country=false&media_type=all&search_type=page&view_all_page_id="


class B:
    def __init__(self):
        self.p = sync_playwright().start(); self.b = self.p.chromium.launch(headless=True); self.n = 0; self.ctx = None; self._novo()
    def _novo(self):
        if self.ctx: self.ctx.close()
        self.ctx = self.b.new_context(locale="pt-PT", timezone_id="Europe/Lisbon", extra_http_headers={"Accept-Language": "pt-PT,pt;q=0.9"})
        self.pg = self.ctx.new_page()
        try: self.pg.goto(URL + POS, wait_until="domcontentloaded", timeout=45000); time.sleep(5)
        except Exception: pass
    def js(self, expr):
        return self.pg.evaluate(expr if expr.strip().startswith("(") or "=>" in expr else "() => " + expr)
    def ir(self, url, espera=4.0, ate=None):
        self.n += 1
        if self.n % 40 == 0: self._novo()
        self.pg.goto(url, wait_until="domcontentloaded", timeout=45000); time.sleep(espera)
        if ate:
            for _ in range(20):
                try:
                    if self.js(ate): break
                except Exception:
                    pass
                time.sleep(0.7)


def contar(b, pid):
    b.ir("https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country=ALL&is_targeted_country=false&media_type=all&search_type=page&view_all_page_id=" + pid, 3.5,
         ate="/resultados?|Nenhum anúncio|Nenhum dos anúncios corresponde|Não há anúncios|não corresponde/i.test(document.body.innerText)")
    t = b.js("document.body.innerText")
    if re.search(r"captcha|Confirma que és|não és um robô", t, re.I): raise RuntimeError("BLOQUEIO captcha")
    m = re.search(r"~?\s?([\d.]+)\s+resultados?", t)
    total = int(m.group(1).replace(".", "")) if m else 0
    if not m and not re.search(r"Nenhum anúncio|Nenhum dos anúncios corresponde|Não há anúncios|não corresponde", t): return None
    ativos = len(re.findall(r"(?m)^Ativo$", t)); cartoes = ativos + len(re.findall(r"(?m)^Inativo$", t))
    datas = [time.strptime(d, "%d/%m/%Y") for d in re.findall(r"(?:Começou a ser publicado a |\n)(\d{2}/\d{2}/\d{4})(?: – \d{2}/\d{2}/\d{4})?\n", t)]
    ultimo = time.strftime("%Y-%m-%d", max(datas)) if datas else ""
    if total > cartoes and total > 0:  # nem todos os cartões estão na página: contar só os ativos
        b.ir("https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=ALL&is_targeted_country=false&media_type=all&search_type=page&view_all_page_id=" + pid, 3.5,
             ate="/resultados?|Nenhum anúncio|Nenhum dos anúncios corresponde|Não há anúncios|não corresponde/i.test(document.body.innerText)")
        m2 = re.search(r"~?\s?([\d.]+)\s+resultados?", b.js("document.body.innerText"))
        ativos = int(m2.group(1).replace(".", "")) if m2 else 0
    return ativos, total, ultimo


def ok(b):
    try: c = contar(b, POS)
    except Exception: c = None
    return bool(c) and c[1] > 0


lote, k, n, saida = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
P = [p for i, p in enumerate(json.load(open(lote))) if i % n == k]
pausa = float(sys.argv[5]) if len(sys.argv) > 5 else 12
b = B(); feitos = []; prov = []
print("lote", len(P), flush=True)
if not ok(b): print("controlo inicial falhou", flush=True); P = []
for x, pid in enumerate(P):
    try: c = contar(b, pid)
    except Exception as e: print("erro", pid, str(e)[:80], flush=True); c = None
    if c is not None: prov.append({"page_id": pid, "ativos": c[0], "total": c[1], "ultimo": c[2], "em": time.strftime("%F %T")})
    time.sleep(pausa)
    if (x + 1) % 25 == 0 or x == len(P) - 1:
        if ok(b): feitos += prov; prov = []
        else:
            feitos += [y for y in prov if y["total"]]; print("controlo falhou depois de", x + 1, "· zeros desde o último controlo bom descartados", flush=True); break
json.dump(feitos, open(saida, "w")); print("contadas", len(feitos), "de", len(P), flush=True)
