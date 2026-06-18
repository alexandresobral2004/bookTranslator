import sys
import os

def check_imports():
    errors = 0
    print("=== Teste de Importação de Bibliotecas ===")
    
    # 1. PyMuPDF (fitz)
    try:
        import fitz
        print(f"[OK] PyMuPDF (fitz) importado com sucesso. Versão: {fitz.__doc__.split()[1] if fitz.__doc__ else 'N/A'}")
    except Exception as e:
        print(f"[FAIL] Falha ao importar PyMuPDF: {e}")
        errors += 1

    # 2. PyTorch
    try:
        import torch
        device = "cpu"
        if torch.cuda.is_available():
            device = "cuda"
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            device = "mps"
        print(f"[OK] PyTorch importado com sucesso. Versão: {torch.__version__}. Dispositivo local disponível: {device}")
    except Exception as e:
        print(f"[FAIL] Falha ao importar PyTorch: {e}")
        errors += 1

    # 3. Transformers & Sentencepiece
    try:
        import transformers
        import sentencepiece
        print(f"[OK] Transformers importado com sucesso. Versão: {transformers.__version__}")
        print(f"[OK] Sentencepiece importado com sucesso.")
    except Exception as e:
        print(f"[FAIL] Falha ao importar Transformers/Sentencepiece: {e}")
        errors += 1

    # 4. FAISS & Sentence-Transformers
    try:
        import faiss
        from sentence_transformers import SentenceTransformer
        print(f"[OK] FAISS importado com sucesso. Versão: {faiss.__version__}")
        print(f"[OK] Sentence-Transformers importado com sucesso.")
    except Exception as e:
        print(f"[FAIL] Falha ao importar FAISS/Sentence-Transformers: {e}")
        errors += 1

    # 5. WeasyPrint
    try:
        from weasyprint import HTML
        # Tenta compilar um HTML básico para validar as dependências do Cairo/Pango
        html_str = "<html><body><h1>Smoke Test</h1></body></html>"
        HTML(string=html_str).write_pdf("/tmp/smoke_test_weasyprint.pdf" if os.path.exists("/tmp") else "data/smoke_test_weasyprint.pdf")
        print(f"[OK] WeasyPrint importado e compilado com sucesso.")
    except Exception as e:
        print(f"[FAIL] Falha ao importar ou compilar com WeasyPrint (verifique pango/cairo): {e}")
        errors += 1

    print("==========================================")
    if errors == 0:
        print("Sucesso! Todas as bibliotecas críticas estão prontas para execução local.")
        sys.exit(0)
    else:
        print(f"Erro: {errors} biblioteca(s) falharam no teste. Verifique dependências de sistema.")
        sys.exit(1)

if __name__ == "__main__":
    check_imports()
