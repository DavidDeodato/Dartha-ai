import os
import pkg_resources
import sys
import subprocess

# Lista de pacotes que devem sempre ser incluídos se instalados
ESSENTIAL_PACKAGES = ["uvicorn", "gunicorn", "httpx", "asyncpg", "python-dotenv", "PyJWT", "faiss-cpu", "langchain_community", "langchain_text_splitters", "langchain_openai", "python-docx"]

def get_installed_packages():
    """Obtém todas as bibliotecas instaladas com suas versões."""
    return {pkg.key: pkg.version for pkg in pkg_resources.working_set}

def is_standard_library(module_name):
    """Verifica se um módulo faz parte da biblioteca padrão do Python."""
    if module_name in sys.builtin_module_names:
        return True
    try:
        spec = __import__('importlib').util.find_spec(module_name)
        return spec is not None and spec.origin is not None and "site-packages" not in spec.origin
    except ModuleNotFoundError:
        return False

def extract_imports_from_files(directory, extensions=(".py",)):
    """Extrai todos os módulos importados dos arquivos do projeto."""
    imported_modules = set()

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(extensions):
                file_path = os.path.join(root, file)
                with open(file_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("import ") or line.startswith("from "):
                            parts = line.split()
                            module_name = parts[1].split(".")[0] if "import" in parts else parts[0]
                            imported_modules.add(module_name)

    return imported_modules

def generate_requirements_txt(output_file="requirements.txt"):
    """Gera um requirements.txt preciso com base nas bibliotecas realmente usadas no projeto."""
    installed_packages = get_installed_packages()
    imported_modules = extract_imports_from_files(os.getcwd())

    used_packages = {}
    for module in imported_modules:
        if module in installed_packages and not is_standard_library(module):
            used_packages[module] = installed_packages[module]

    # Adicionar pacotes essenciais se estiverem instalados
    for essential in ESSENTIAL_PACKAGES:
        if essential in installed_packages and essential not in used_packages:
            used_packages[essential] = installed_packages[essential]

    # Verificar se há conflitos de versões (opcional)
    outdated_packages = subprocess.run([sys.executable, "-m", "pip", "list", "--outdated"],
                                       capture_output=True, text=True).stdout

    print("\n📌 Pacotes detectados no projeto:")
    for package, version in used_packages.items():
        status = "⚠️ Desatualizado" if package in outdated_packages else "✅ Ok"
        print(f"  - {package}=={version} {status}")

    with open(output_file, "w") as f:
        for package, version in sorted(used_packages.items()):
            f.write(f"{package}=={version}\n")

    print(f"\n✅ Arquivo '{output_file}' atualizado com sucesso!")

if __name__ == "__main__":
    generate_requirements_txt()
