# importaciones
from flask import Flask, jsonify, request
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

Datos = pd.read_excel("./prueba.xlsx")
def convertStrToDate(date):
    if(type(date)==datetime):
        return date
    else:
        if(len(date)>=21):
            return datetime.strptime(date, '%m/%d/%Y %I:%M:%S %p')
        return datetime.strptime(date, '%m/%d/%Y')

def date(str):
    list = []
    x = 0
    for fecha in str:
        list.append(convertStrToDate(fecha))
    return pd.Series(list)

def calculateminutes(list):
    l = []
    for date in list:
        l.append(int(date.seconds / 60))
    return pd.Series(l)


app = Flask(__name__)


@app.route('/ping', methods=['GET'])
def ping():
    fechas = Datos[['Desde*','Hasta*','Subcódigo*','P/N*']].copy()
    fechas['Tiempo'] = date(fechas['Hasta*'])-date(fechas['Desde*'])
    fechas['minutes']= calculateminutes(fechas['Tiempo'])
    json = fechas.loc[fechas['P/N*']=='N']
    print(json)
    new = json.groupby(['Subcódigo*'])['minutes'].agg('sum')
    new2 = json.groupby('Subcódigo*')['minutes'].sum().reset_index()
    new3 = json.groupby('Subcódigo*').sum().reset_index()
    list = new3.to_dict('records')
    # parsed = json.loads(result)
    # json.dumps(parsed, indent=4)

    print(new3)
    print(list)
    # result = jsonify(new3)
    # print(result)
    return jsonify({'data':list})


if __name__ == '__main__':
    app.run(debug=True,port=4000)


