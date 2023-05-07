import os
import json
from datetime import datetime
from time import sleep

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def load_inputs_db(filepath='inputs.csv'):
    data = pd.read_csv(filepath, header=0)
    return data


def load_registro_db(filepath='registro.csv'):
    if os.path.exists(filepath):
        data = pd.read_csv(filepath, header=0)
    else:
        # Si es la primera vez que creo un registro. Creo un pandas vacio
        data = pd.DataFrame(columns=['fecha', 'telefono', 'saldo', 'operador'])
    return data


def save_registro_db(df, filepath='registro.csv'):
    df.to_csv(filepath, index=False)
    print('Informacion de operaciones exportada a registro.csv')


def agregar_registro(telefono, saldo, operador, filepath='registro.csv'):
    registro = load_registro_db(filepath)
    nuevo_registro = {
        'fecha': datetime.now(),
        'telefono': telefono,
        'saldo': saldo,
        'operador': operador,
    }
    registro = pd.concat([registro, pd.DataFrame(
        nuevo_registro, index=[0])], ignore_index=True, axis=0)
    print(registro)
    save_registro_db(registro, filepath)


def get_login_credentials(filepath='credentials.json'):
    with open(filepath, 'r') as f:
        credentials = json.load(f)
    return credentials


def login(driver):
    """
    Funcion para logearse en el sitio de Regargas
    """
    login_data = get_login_credentials()
    search_field = driver.find_element(By.XPATH, '//*[@id="Usuario"]')
    search_field.send_keys(login_data['usuario'])
    search_field = driver.find_element(By.XPATH, '//*[@id="Clave"]')
    search_field.send_keys(login_data['password'])
    search_field = driver.find_element(By.XPATH, '//*[@id="PV"]')
    search_field.send_keys(login_data['pv'])
    search_field = driver.find_element(
        By.XPATH, '//*[@id="submitbuttoninvisible"]')
    search_field.click()
    # Agrego sleep por las dudas nomas. Se puede disminuir este tiempo
    sleep(0.5)
    return driver


def driver_elegir_proveedor(driver, proveedor):
    """
    Elegir el proveedor de celulares que se desea operar.
    En este caso vamos por Movistar.
    TODO: Completar con otros proveedores buscando la ruta PATH
    de cada uno de ellos.
    TODO: No sé si esa ruta es de movistar, inventé que sea de movistar.
    """
    if proveedor == 'movistar':
        search_field = driver.find_element(
            By.XPATH, '//*[@id="Online"]/div[1]/div/div[2]/div')
    else:
        print('Proveedor no conocido')
        return
    search_field.click()
    # Agrego sleep por las dudas nomas. Se puede disminuir este tiempo
    sleep(0.5)
    return driver


def cargar_saldo(driver, celular, saldo, proveedor):
    """
    Carga saldo a un número de celular.
    El driver (selenium) ya tiene que estar logeado y en la página principal.
    Primero seleccionamos el proveedor donde queremos cargar saldo. Esta opción
    Al finalizar vuelve a la ventana de operadores si la operacion fue correcta.
    """
    driver = driver_elegir_proveedor(driver, proveedor)
    search_field = driver.find_element(By.XPATH, '//*[@id="importe"]')
    search_field.send_keys(str(saldo))
    search_field = driver.find_element(By.XPATH, '//*[@id="identificacion"]')
    input_ani = driver.find_element(By.XPATH, '//*[@id="identificacion"]')
    input_ani.send_keys(str(celular))
    search_field = driver.find_element(By.XPATH, '//*[@id="btnConfirmar"]/i')
    search_field.click()
    try:
        WebDriverWait(driver, 3).until(EC.alert_is_present(),
                                       'Me canse de esperar que aparezca la alerta')
        alt = driver.switch_to.alert
        alt.accept()
    except Exception:
        # No pude terminar la opeacion.. salgo de la funcion
        return
    try:
        # Si la operacion no fue exitosa, no hay boton volver y esto tira error.
        search_field = driver.find_element(By.XPATH, '//a[@id="btnVolver"]')
        search_field.click()
        # actualizo el registro de operacions si no tuve error en la operacion
        agregar_registro(celular, saldo, proveedor)
    except Exception:
        # la operacion no fue exitosa. Volvemos al menu principal
        search_field = driver.find_element(
            By.XPATH, '//button[@id="btnCancelar"]')
        search_field.click()


def cargar_saldos_csv(driver, csv_filepath='inputs.csv'):
    """
    Iteramos sobre el csv con los celulares y montos a cargar
    y le agregamos el saldo deseado a cada uno de ellos.
    """
    df = load_inputs_db(csv_filepath)
    for i in range(len(df)):
        telefono = df.iloc[i]['celular']
        saldo = df.iloc[i]['saldo']
        operador = df.iloc[i]['operador']
        cargar_saldo(driver, telefono, saldo, operador)


if __name__ == '__main__':
    driver = webdriver.Chrome()
    driver.get('https://net.cargavirtual.com/Account/LoginNuevo')
    driver = login(driver)
    cargar_saldos_csv(driver)
