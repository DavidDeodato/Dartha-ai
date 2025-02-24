#!/bin/bash

# 🟢 Atualiza a lista de pacotes
apt-get update

# 🟢 Instala o Python 3 e o Pip caso não estejam instalados
apt-get install -y python3 python3-pip

# 🟢 Define "python" para apontar para "python3"
ln -s /usr/bin/python3 /usr/bin/python

# 🟢 Atualiza o Pip
python3 -m ensurepip --default-pip
python3 -m pip install --upgrade pip

# 🟢 Instala as dependências do projeto
pip install -r requirements.txt
