# importaciones
from flask import Flask, jsonify, request
import pandas as pd
from datetime import datetime

app = Flask(__name__)

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


@app.route('/', methods=['GET'])
def home():
    return jsonify({'message':'Api init'})

@app.route('/', methods=['POST'])
def homepost():
    return jsonify({'message':'please send all data'})

@app.route('/file', methods=['POST'])
def recivedfile():
    file = request.files["filename"]
    if file:
        archivo = pd.read_excel(file)
        fechas = archivo[['Desde*','Hasta*','Subcódigo*','P/N*']].copy()
        fechas['Tiempo'] = date(fechas['Hasta*'])-date(fechas['Desde*'])
        fechas['minutes']= calculateminutes(fechas['Tiempo'])
        data = fechas.loc[fechas['P/N*']=='N'].groupby('Subcódigo*').sum().reset_index().to_dict('records')
        return jsonify({'data':data})
    return jsonify({'message':'please all data'})

if __name__ == '__main__':
    app.run(debug=True,port=4000)


