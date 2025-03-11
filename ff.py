import pkg_resources

def parse_pkg_name(line: str) -> str:
    """
    Dado uma linha do requirements.txt (ex: 'requests>=2.28.2'),
    retorna o nome do pacote (ex: 'requests').
    """
    line = line.strip()
    # Se houver comentário ou linha vazia, retornamos vazio
    if not line or line.startswith("#"):
        return ""

    # Remove extras (ex: 'package[extra]')
    if "[" in line:
        line = line.split("[")[0]

    # Lista de possíveis operadores de versão
    version_operators = ["==", ">=", "<=", "~=", "!=", "<", ">"]

    for op in version_operators:
        if op in line:
            # Pega tudo antes do operador
            return line.split(op)[0].strip()
    # Se não encontrou operador, pode ser só o nome
    return line

def main():
    try:
        with open("requirements.txt", "r") as f:
            lines = f.read().splitlines()
    except FileNotFoundError:
        print("❌ ERRO: Não foi encontrado o arquivo 'requirements.txt' na raiz do projeto.")
        return

    print("=== Checando versões instaladas dos pacotes listados em requirements.txt ===\n")

    for line in lines:
        pkg_name = parse_pkg_name(line)
        if not pkg_name:
            # Linha vazia ou comentário
            continue
        try:
            dist = pkg_resources.get_distribution(pkg_name)
            print(f"{pkg_name} => INSTALADO: versão {dist.version}")
        except pkg_resources.DistributionNotFound:
            print(f"{pkg_name} => NÃO INSTALADO")

if __name__ == "__main__":
    main()
