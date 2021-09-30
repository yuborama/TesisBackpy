# importaciones
print("hola1")
from flask import Flask, jsonify, request,send_file
from flask_cors import CORS
import pandas as pd
from datetime import datetime
from io import BytesIO
import re
from xlsxwriter import Workbook
# import pipreqs
# print(pipreqs --print ./);
# from werkzeug.utils import send_file

app = Flask(__name__)

CORS(app)
def convertdatestr(x):
    y = pd.to_datetime(str(x),format='%Y-%m-%d %H:%M:%S',errors='raise')
    return y.strftime('%Y-%d-%m %H:%M:%S')

def diff(vx, vy, dx, dy, dif):
    if(vx == 0 and vy == 0):  
        if(dx > dy):
            return dy
        else:
            return dx
    return dif

roundnumber = lambda x: round(x, 2)
converterdatastr = lambda x : pd.to_datetime(str(x),format='%Y-%m-%d %H:%M:%S',errors='ignore') 
converter = lambda x : ((pd.to_datetime(x,format='%m/%d/%Y %I:%M:%S %p',errors='ignore')) 
                        if re.findall('[AMPM]$',str(x)) 
                        else ((pd.to_datetime(x,format='%Y-%d-%m %H:%M:%S',errors='ignore')) 
                               if re.findall('-',str(x)) 
                               else (pd.to_datetime(str(x),errors='ignore'))
                        ))
# funcion devoler dataframe segun colunmas
def df_columns(file,columns):
    Datos = pd.read_excel(file, parse_dates=False,dtype={'Hasta*':'str','Desde*':'str'})    
    namecolumns = [x.strip() for x in list(Datos.columns)]
    Datos.columns=namecolumns
    return Datos[columns]

def calculate_velocity(df):
    print("hola8")
    print("hola9")
    df['diferencia'] = df['Hasta*'].apply(converter)-df['Desde*'].apply(converter)
    print("hola10")
    df['perforacion']= df['MD to (ft)']-df['MD from (ft)']
    df2 = df.loc[df['P/N*']=='P'].groupby(['Subcódigo*']).agg({'diferencia':'sum','perforacion':'sum'}).reset_index()
    df2['velocidad'] = (df2['perforacion']/(df2['diferencia'].dt.total_seconds()/3600))
    return df2[['Subcódigo*','perforacion','velocidad','diferencia']]

def mergedfs(df,df2):
    df3 = pd.merge(df,df2,how='outer',on=['Subcódigo*'])
    # print('tipos', df3.dtypes)
    cond=(df3['velocidad_y']>df3['velocidad_x'])| df3['velocidad_x'].isna()
    df3['velocidad'] = df3['velocidad_y'].where(cond, df3['velocidad_x'])
    df3['perforacion'] = df3['perforacion_y'].where(cond, df3['perforacion_x'])
    df3['diferencia'] = df3['diferencia_y'].where(cond, df3['diferencia_x'])
    df3['diferencia'] = ([
        diff(vx=df3['velocidad_x'][n], 
             vy=df3['velocidad_y'][n],
             dx=df3['diferencia_x'][n],
             dy=df3['diferencia_y'][n], 
             dif=df3['diferencia'][n])
        for n in range(len(df3['diferencia']))
    ])
    return df3[['Subcódigo*','perforacion','velocidad','diferencia']]

def export_df(df):
    df['Desde*'] = pd.to_datetime('today').normalize()
    df['Hasta*'] = (pd.to_datetime('today').normalize()+df['diferencia'])
    df['Desde*'] = df['Desde*'].apply(convertdatestr)
    df['Hasta*'] = df['Hasta*'].apply(convertdatestr)
    df['MD from (ft)'] = 0
    df['P/N*'] = 'P'
    df = df.rename(columns={'perforacion':'MD to (ft)'})
    # filta los que tienen valor
    # df = df.loc[df['MD to (ft)'] != 0]
    return df[['Desde*','Hasta*','Subcódigo*','P/N*','MD from (ft)','MD to (ft)']]

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
    if request.files:
        files = request.files.getlist('filename')
        if files:
            datalist = []
            for file in files:
                fechas = df_columns(file,['Desde*','Hasta*','Subcódigo*','P/N*','MD from (ft)','MD to (ft)'])
                fechas['diferencia'] = fechas['Hasta*'].apply(converter)-fechas['Desde*'].apply(converter)
                fechas['hours']= fechas['diferencia'].dt.total_seconds()/3600
                fechas['hours'] =fechas['hours'].apply(roundnumber)
                data = fechas.loc[fechas['P/N*']=='P',['Subcódigo*','hours']].groupby('Subcódigo*').sum().reset_index().to_dict('records')
                dicty ={'File':file.filename,"datos":data}
                datalist.append(dicty)
            return jsonify({'data':datalist})
        return jsonify({'message':'please all data'})
    return jsonify({'message':'upload files'})

@app.route('/filebase',methods=['POST'])
def donwload():
    files = request.files.getlist('filename')
    if files:
        df_1 = pd.DataFrame(columns=['Desde*','Hasta*','Subcódigo*','P/N*','MD from (ft)','MD to (ft)'])
        print("names files")
        print(files)
        for file in files:
            if (df_1.empty==False):
                print('entro if')
                # print("file: ",file)
                df_2 = df_columns(file,['Desde*','Hasta*','Subcódigo*','P/N*','MD from (ft)','MD to (ft)'])
                df2 = calculate_velocity(df_2)
                print('miradme', df2.dtypes)
                df_1 = mergedfs(df_1,df2)
            else:
                print('entro else')
                df_1=df_columns(file,['Desde*','Hasta*','Subcódigo*','P/N*','MD from (ft)','MD to (ft)'])
                df_1 = calculate_velocity(df_1)
        df_1 = export_df(df_1)
        print('df\n',df_1.dtypes)
        print(df_1) 
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        df_1.to_excel(writer, startrow = 0, merge_cells = False, sheet_name = "Sheet_1", index=False)
        # workbook = writer.book
        # worksheet = writer.sheets["Sheet_1"]
        # format = workbook.add_format()
        # format.set_bg_color('#eeeeee')
        # worksheet.set_column(0,9,28)

        #the writer has done its job
        writer.close()
        #go back to the beginning of the stream
        output.seek(0)
        #finally return the file
        return send_file(output, mimetype = 'application/ms-excel', as_attachment=True, download_name="base.xlsx")
    return({'message':'no se encuentra files'})


if __name__ == '__main__':
    app.run(debug=True,port=4000)


