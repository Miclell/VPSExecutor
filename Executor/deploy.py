import os
import subprocess
import configparser
import shutil
import time

def RunCommand(command, cwd=None):
    result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd)
    print(result.stdout.decode())
    if result.stderr:
        print(result.stderr.decode())

def InstallDocker():
    print("Обновление пакетов...")
    RunCommand("sudo apt update")
    print("Установка Docker...")
    RunCommand("sudo apt install -y docker.io")
    print("Добавление пользователя в группу Docker...")
    RunCommand(f"sudo usermod -aG docker $(whoami)")
    print("Перезапуск Docker...")
    RunCommand("sudo systemctl restart docker")

def CreateHashedPassword(username, password):
    command = "apt-get install -y apache2-utils"
    RunCommand(command)

    command = f"htpasswd -nb {username} {password}"
    result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    hashedPassword = result.stdout.decode().strip()
    hashedPassword = hashedPassword.replace('$', '$$')
    return hashedPassword

def InstallTraefik(repoPath, email, host, username, password):
    print("Установка Traefik...")
    traefikDir = os.path.join(repoPath, "Infra", "Traefik")

    hashedPassword = CreateHashedPassword(username, password)

    with open(os.path.join(traefikDir, ".env"), "w") as f:
        f.write(f"EMAIL={email}\n")
        f.write(f"HOST={host}\n")
        f.write(f"HTPASSWD={hashedPassword}\n")

def InstallPortainer(repoPath, host):
    print("Установка Portainer...")
    portainerDir = os.path.join(repoPath, "Infra", "Portainer")

    with open(os.path.join(portainerDir, ".env"), "w") as f:
        f.write(f"HOST={host}\n")

def CopyDirectories(src, dst):
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)

def Main():
    repoPath = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

    configPath = os.path.join(repoPath, 'config.ini')
    config = configparser.ConfigParser()
    config.read(configPath)

    InstallDocker()

    email = config.get('Email', 'email')
    mainHost = config.get('MainHost', 'host')
    traefikHost = config.get('Traefik', 'host')
    traefikLogin = config.get('Traefik', 'login')
    traefikPassword = config.get('Traefik', 'password')

    traefikFullHost = f"{traefikHost}.{mainHost}"
    portainerFullHost = f"{config.get('Portainer', 'host')}.{mainHost}"        

    if config.getboolean('Traefik', 'install'):
        InstallTraefik(repoPath, email, traefikFullHost, traefikLogin, traefikPassword)
        CopyDirectories(os.path.join(repoPath, "Infra", "Traefik"), "../../Infra/Traefik")
        RunCommand("docker-compose up -d", cwd="../Infra/Traefik")
    if config.getboolean('Portainer', 'install'):
        InstallPortainer(repoPath, portainerFullHost)
        CopyDirectories(os.path.join(repoPath, "Infra", "Portainer"), "../../Infra/Portainer")
        RunCommand("docker-compose up -d", cwd="../Infra/Portainer")

    installMainerChoice = input("Установить Mainer? (y/n): ").lower()
    if installMainerChoice == 'y':
        CopyDirectories(os.path.join(repoPath, "Utils", "Mainer"), "../Utils/Mainer")
        RunCommand("docker-compose up -d", cwd="../Utils/Mainer")
        print("Mainer успешно установлен!")
    else:
        print("Mainer успешно установлен!")
        time.sleep(1)
        print("Ти лох, это джоке:)")

if __name__ == "__main__":
    Main()
