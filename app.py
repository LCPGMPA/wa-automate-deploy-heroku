import asyncio
from wa_automate_socket_client import SocketClient
import logging
import time as ti
from pymongo import MongoClient
from datetime import datetime, timedelta, time
import re
import pandas as pd
import os
import sys
import gspread
from gspread.exceptions import WorksheetNotFound
from oauth2client.service_account import ServiceAccountCredentials
from apscheduler.schedulers.background import BackgroundScheduler
import gc

# MONGODB
# MongoDB connection
mongo_uri = os.getenv("MONGO_URI")
cluster = MongoClient(mongo_uri)
db = cluster["LCclinica"]
users = db["users"]
bot_status = db['bot_status']
blacklist = db['blacklist']
orders = db['orders']


credentials_info = {
    "type": os.getenv("GOOGLE_TYPE"),
    "project_id": os.getenv("GOOGLE_PROJECT_ID"),
    "private_key_id": os.getenv("GOOGLE_PRIVATE_KEY_ID"),
    "private_key": os.getenv("GOOGLE_PRIVATE_KEY").replace("\\n", "\n"),  # Replace escaped newlines
    "client_email": os.getenv("GOOGLE_CLIENT_EMAIL"),
    "client_id": os.getenv("GOOGLE_CLIENT_ID"),
    "auth_uri": os.getenv("GOOGLE_AUTH_URI"),
    "token_uri": os.getenv("GOOGLE_TOKEN_URI"),
    "auth_provider_x509_cert_url": os.getenv("GOOGLE_AUTH_PROVIDER_X509_CERT_URL"),
    "client_x509_cert_url": os.getenv("GOOGLE_CLIENT_X509_CERT_URL"),
    "universe_domain": os.getenv("GOOGLE_UNIVERSE_DOMAIN")
}





#Sheet File access and location
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_info, scope)
client = gspread.authorize(creds)
file_id = os.getenv("FILE_ID")
file_id_2 = os.getenv("FILE_ID_2")

# Procedure list
procedures = {
        "Limpeza_de_Pele": {"duration": 7, "can_do": 3, },
        "Cílios": {"duration": 2, "can_do": 1},
        "Sobrancelhas": {"duration": 2, "can_do": 1}, 
        "Procedimentos_Labial": {"duration": 1, "can_do": 3},
        "Peeling": {"duration": 1, "can_do": 3},
        # Add more procedures as needed
    }

Cílios = {"Cílios: Jade": {"duration": 7, "can_do": 2, "description": "Técnica com fios de pura seda leve e sofisticado voltado para quem deseja um olhar com volume natural.\n\nDisponivel nas cores: loiro, ruivo ou preto.\n\n Valor do investimento: R$ 210,00"},
        "Cílios: Fio a Fio (clássico)": {"duration": 7, "can_do": 2, "description": "Aplicação de um único fio com efeito hiper natural de fios sintéticos para alongar olhar.\n\n Valor do investimento: R$ 170,00"},
        "Cílios: Híbrido": {"duration": 7, "can_do": 2, "description": "Volume e preenchimento com leque de fios (3 a 6 fios de seda) não tocam na raiz montados na hora.\n\n Valor do investimento: R$ 170,00"},
        "Cílios: Volume Brasileiro": {"duration": 7, "can_do": 2, "description": "Fio em formato de Y, efeito natural e leve com pura seda.\n\n Valor do investimento: R$ 170,00"},
        "Cílios: Fox Eyes": {"duration": 7, "can_do": 2, "description": "Técnica que busca criar um olhar mais alongado e 'puxado' para os cantos externos dos olhos, semelhante ao olhar felino.\n\nDisponivel nas cores: loiro, ruivo ou preto.\n\n Valor do investimento: R$ 200,00"},
        "Cílios: Volume Russo": {"duration": 8, "can_do": 2, "description": "Técnica com leque de fios de seda, entrega volume extremo e fios mais encorpados do que nunca. Extremamente leve e sem agredir os fios naturais\n\n Valor do investimento: R$ 210,00"},
        "Cílios: Mega Volume": {"duration": 8, "can_do": 2, "description": "Técnica alcança densidade e profundidade imbatíveis nos cílios, criando um olhar dramático e intenso com conforto e a segurança para saúde dos seus olhos. Efeito cílios postiços.\n\n Valor do investimento: R$ 230,00"},
        "LASH BEAUTY": {"duration": 6, "can_do": 3, "description": "O procedimento consiste em curvar os cílios naturais e deixá-los mais alongados. Esse alongamento é realizado desde a raiz do seu fio até as pontas dos cílios. Com hidratação e recuperação dos fios.\n\n*Com durabilidade de 4 a 6 semanas.*\n\n Valor do investimento: R$ 180,00"}
        }

Limpeza_de_Pele = {
        "Limpeza de Pele: PREMIUM": {"duration": 7, "can_do": 3, "description": '*Limpeza de Pele PREMIUM* tem como objetivo remover cravos fazendo um detox da pele.\nCom alta concenração de etivos e equipamentos de última geração e tecnologia para nutrir e cuidar da sua pele.\n\n Valor do investimento: R$ 220,00'},
        "Limpeza de Pele: DESINCRUSTANTE": {"duration": 7, "can_do": 3, "description": "*Limpeza de Pele DESINCRUSTANTE* é voltada para peles acneicas e oleosas. Além de ativos a limpeza de pele desincrustante conta com aparelho com corrente elétrica que faz uma emoliência mais profunda na pele transformando o sebo em sabão, prolongando sua pele mais hidratada. Reduzindo a oleosidade.\n\n Valor do investimento: R$ 240,00"},
        "Limpeza de Pele: GLOW MASTER": {"duration": 8, "can_do": 3, "description": "*Limpeza de Pele GLOW MASTER* é uma técnica desenvolvida para devolver o brilho, hidratação e glow de forma instantâneo na pele. Além de remover cravos, espinhas e melhorar a barreira cutânea da pele por repor vitaminas na pele. A sessão conta com aplicação de cromoterapia e aromaterapia para seu momento de relaxamento.\n\n Valor do investimento: R$ 260,00"},
        "REVITALIZAÇAO FACIAL": {"duration": 7, "can_do": 3, "description": "A revitalização facial tem como objetivo regenerar pele, nutrir e manter com mais luminosidade, elasticidade e hidratação. Ajuda proteger a pele da poluição, melhora a textura e a maciez da pele.\n\n Valor do investimento: R$ 280,00"},
        }

Sobrancelhas = {
        "Design Sobrancelha: INFINITY FULL": {"duration": 2, "can_do": 1, "description": 'Design de sobrancelha personalizado com coloração temporário e ativos que proporcionam volume natural nas sobrancelhas. (linha, pinça ou navalha)\n\n Valor do investimento: R$ 60,00'},
        "Design Sobrancelha: HENNA SOFT": {"duration": 2, "can_do": 1, "description": "Design de sobrancelha personalizado com henna em um efeito de maquiagem hiper alinhado.\n\n Valor do investimento: R$ 50,00"},
        "Design Sobrancelha: DESIGN STRATÉGICO": {"duration": 2, "can_do": 1, "description": "Design de sobrancelha personalizado com simetria facial para proporcionar um olhar harmônico e natural. \n\n Valor do investimento: R$ 40,00"},
        "Micropigmentação: NANO FIOS": {"duration": 8, "can_do": 3, "description": 'Técnica de implantação de cor, formando tramas naturais como se fossem os fios naturais da sobrancelha.\n*Retoque após 30 dias incluso*\n\n*Com durabilidade de 8 a 18 meses.* (Não é tatuagem!)\n\n Valor do investimento: R$ 700,00'},
        "Micropigmentação: SHADOW SOFT": {"duration": 8, "can_do": 1, "description": "Técnica de micropigmentação que preenche as sobrancelhas com pigmento, criando um efeito de sombreamento e suavidade que imita a maquiagem\n*Retoque após 30 dias incluso*\n\n*Com durabilidade de 1 ano e meio a 2 anos.* (Não é tatuagem!)\n\n Valor do investimento: R$ 800,00"},
        "Micropigmentação: SOFT POWDER BROWS": {"duration": 8, "can_do": 1, "description": "Técnica Europea de micropigmentação que tem com objetivo dar volume com pixels, encorpando a sobrancelha, diminuindo falhas, deixando um ton muito natural e simétrico.\n*Retoque após 30 dias incluso*\n\n*Com durabilidade de 1 ano e meio a 2 anos.* (Não é tatuagem!)\n\n Valor do investimento: R$ 900,00"},
        "BROW BEAUTY": {"duration": 4, "can_do": 1, "description": "Técnica de laminagem das sobrancelhas, criando um efeito de preenchimento e volume natural das sobrancelhas em efeito fio a fio com hidratação e nutrição dos fios.\n*Design personalizado mais pigmento temporário incluso*\n\n*Com durabilidade de 4 a 6 semanas.*\n\n Valor do investimento: R$ 180,00"},
        "BROWS REPAIR": {"duration": 3, "can_do": 1, "description": "Técnica de microagulhamento das sobrancelhas com blend de vitaminas e fatores de crescimento natural dos fios, para recuperar e reconstruir as suas sobrancelhas de forma natural e saudável.\n\n Valor do investimento: R$ 100,00 \n\n Pacote de 3 sessões: R$ 240,00"},
        "BROWS TOTAL COLOR (ruivas e loiras)": {"duration": 3, "can_do": 1, "description": "Procedimento para tonalizar o tom dos fios exatamente proporcional ao tom capilar. Por exemplo: Ruivos, loiros, castanhos. Design incluso.\n\n Valor do investimento: R$ 100,00."},
        }

Procedimentos_Labial = {
        "Micropigmentação: NEUTRA LIPS": {"duration": 7, "can_do": 1, "description": "Técnica incrível para os lábios que desejam apresentar uma coloração mais uniforme e natural. Manchas escuras, descolorações e outros problemas de pigmentação são minimizados ou completamente eliminados.\n\n Valor do investimento: R$ 900,00 (já com retoque incluso após 30 dias!)"},
        "Micropigmentação: LCOLOR LIPS": {"duration": 7, "can_do": 1, "description": "Técnica que pode melhorar a assimetria dos lábios, corrigir imperfeições, como cicatrizes ou falta de pigmentação, e criar a ilusão de lábios mais cheios e volumosos. Além disso, a técnica proporciona um visual duradouro, economizando tempo no dia a dia, pois dispensa a aplicação constante de batom. \n\n Valor do investimento: R$ 800,00 (já com retoque incluso!)"},
        "Micropigmentação: ANGEL LIPS": {"duration": 7, "can_do": 1, "description": "Técnica de micropigmentação com volume e naturalidade para lábios sem marcação, com cor suave e natural quem deseja manter lábios com cor em tons suaves e elegantes.\n\n Valor do investimento: R$ 990,00"},
        "Micropigmentação: REVITA LIPS": {"duration": 7, "can_do": 1, "description": "Sabe aquela cor de lábios pálidos ? Apenas querendo um tom de saúde ? Essa técnica é para você em apenas 1 sessão você alcança esse resultado.\n\n Valor do investimento: R$ 480,00"},
        "HYDRABEAUTY": {"duration": 3, "can_do": 3, "description": "Efeito glow deixando seus lábios com aspecto saudável, remove células da pele morta, estímulo do colágeno e da elasticidade da pele. Lábios macios e hidratados. 0 dor e desconforto.\n\n Valor do investimento: R$ 180,00"},
        }

Peeling = {
        "DIAMANTE": {"duration": 4, "can_do": 3, "description": "Procedimento para quem busca uma pele rejuvenescida pois proporciona uma renovação celular, removendo as células mortas da superfície da pele e estimulando novas células. O resultado é uma pele mais fresca e jovem. Além disso, o peeling de diamante pode melhorar significativamente a textura da pele, tornando-a mais lisa e uniforme.\n\n Valor do investimento: R$ 390,00\n\n_(consulte se sua pele realmente está habilitada para realizar o procedimento) Solicite consulta avaliativa!._"},
        "QUÍMICO": {"duration": 4, "can_do": 3, "description": "Tratamento utilizando aplicação de ácidos sobre a pele para retirar as camadas danificadas e promover o crescimento de uma camada lisa, podendo ser feito para eliminar manchas e linhas de expressão, por exemplo de acne.\n\n Valor do investimento: R$ 390,00\n\n_(consulte se sua pele realmente está habilitada para realizar o procedimento) Solicite consulta avaliativa!._"},
        "FÍSICO": {"duration": 4, "can_do": 3, "description": "Sem ácidos, para procedimento totalmente natural. Removendo as células epiteliais mortas e que já foram agredidas por fatores intrínsecos e, principalmente, extrínsecos, o peeling dá lugar a uma pele nova muito mais uniforme, jovem e saudável. Além disso, a reestruturação da pele estimula a produção de colágeno, deixando-a firme, viçosa e rejuvenescida.\n\n Valor do investimento: R$ 420,00\n\n_(consulte se sua pele realmente está habilitada para realizar o procedimento) Solicite consulta avaliativa!._"},
        "PEELING DE HOLLYWOOD": {"duration": 4, "can_do": 3, "description": "O procedimento reduz a aparência de poros dilatados, diminui as linhas de expressão, harmoniza a tonalidade da cor da pele, aumenta a produção de colágeno e elastina e proporciona um efeito de profunda regeneração, deixando a pele mais homogênea e iluminada. Sem dor e desconforto.\n\n Valor do investimento: R$ 580,00\n\n_(consulte se sua pele realmente está habilitada para realizar o procedimento) Solicite consulta avaliativa!._"}, 
        }

# logging.basicConfig(level=logging.DEBUG)
month_translation = {
    "January": "JANEIRO",
    "February": "FEVEREIRO",
    "March": "MARÇO",
    "April": "ABRIL",
    "May": "MAIO",
    "June": "JUNHO",
    "July": "JULHO",
    "August": "AGOSTO",
    "September": "SETEMBRO",
    "October": "OUTUBRO",
    "November": "NOVEMBRO",
    "December": "DEZEMBRO"
}

#BLOCKED NUMBERS MDB
def get_all_blocked_numbers():
    blocked_numbers = blacklist.find({}, {"_id": 0, "blocked_number": 1})
    return [entry["blocked_number"] for entry in blocked_numbers]

#BOT STATUS CREATION MDB
def initialize_bot_status():
    bot_status_collection = db["bot_status"]
        
        # Check if there are any documents in the bot_status collection
    if bot_status_collection.count_documents({}) == 0:
            # Insert a document if the collection is empty
         bot_status_collection.insert_one({
             "bot_id": "whatsapp_bot_1",
             "bot_active": True,
             "last_active": datetime.now()
            })
    else:
        print("Bot status already initialized.")

#BOT STATUS CHECK MDB
def is_bot_active():
    status = bot_status.find_one()
    if status:
        last_human_message = status.get("last_human_message")
        bot_active = status.get("bot_active", True)
        if last_human_message:
            last_human_time = last_human_message
            now = datetime.now()
            if now - last_human_time < timedelta(minutes=15):
                print('Bot inactive: Human intervention was too recent')
                return False
        return bot_active
    return False

#HUMAN INTERVENTION BY PASSCODE MDB
def update_last_human_message():
    now = datetime.now()
    bot_status.update_one({}, {"$set": {"last_human_message": now, "bot_active": True}}, upsert=True)
    print("Human intervention registered")


#VALID DATE CHECKER
def is_valid_date(date_str):
    try:
        datetime.strptime(date_str, "%Y/%m/%d")
        return True
    except ValueError:
        return False

#SHEET READER
def read_sheet(file_id, sheet_name):
    # Set up the credentials and client
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_info, scope)
    client = gspread.authorize(creds)
    
    try:
        # Open the spreadsheet and get the sheet
        sheet = client.open_by_key(file_id).worksheet(sheet_name)
        
        # Get all records and convert to DataFrame
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        
        return df
    
    except WorksheetNotFound:
        return "Sheet not found"

def get_available_times(date_str, procedure_name, can_do, duration, file_id, number):
    # Convert the date string to a datetime object and get the sheet name
    print(f'procedure name: {procedure_name}')
    print(f'duration (in quarters i.e. 15 mins): {duration}')
    date = datetime.strptime(date_str, "%Y/%m/%d")
    sheet_name = date.strftime("%Y-%m")
    print(f'Sheet name: {sheet_name} accessed by: {number}')
    stripped_number = number.lstrip('+')

    try:

        # Read the sheet data
        sheet = read_sheet(file_id, sheet_name)
        
        # Convert 'Data' to datetime and 'Horário' to time
        sheet['Data'] = pd.to_datetime(sheet['Data'])
        sheet['Horário'] = pd.to_datetime(sheet['Horário'], format='%H:%M').dt.time

        # Filter the data for the specified date
        day_data = sheet[sheet['Data'] == pd.to_datetime(date_str)]
        print(day_data)
        contato_count_lo_day = day_data['Contato Lo'].eq(int(stripped_number)).sum()
        print(f"contato_count_lo_day = {contato_count_lo_day}")
        contato_count_lu_day = day_data['Contato Lu'].eq(int(stripped_number)).sum()
        print(f"contato_count_lu_day = {contato_count_lu_day}")

        if (contato_count_lo_day == 1 or contato_count_lo_day == 2) and can_do == 3:
            can_do = 1
            print("can do edited to 1")
        if (contato_count_lu_day == 1 or contato_count_lu_day == 2) and can_do == 3 :
            can_do = 2
            print("can do edited to 2")
        
        if day_data.empty:
            return "No data available for this date."

        # Define the time slots to check
        time_slots = [
            time(8, 0), time(8, 15), time(8, 30), time(8, 45),
            time(9, 0), time(9, 15), time(9, 30), time(9, 45),
            time(10, 0), time(10, 15), time(10, 30), time(10, 45),
            time(11, 0), time(11, 15), time(11, 30), time(11, 45),
            time(12, 0), time(12, 15), time(12, 30), time(12, 45),
            time(13, 0), time(13, 15), time(13, 30), time(13, 45),
            time(14, 0), time(14, 15), time(14, 30), time(14, 45),
            time(15, 0), time(15, 15), time(15, 30), time(15, 45),
            time(16, 0), time(16, 15), time(16, 30), time(16, 45),
            time(17, 0), time(17, 15), time(17, 30), time(17, 45),
            time(18, 00), time(18, 15), time(18, 30), time(18, 45)
        ]
        
        available_slots = []

        # Get the list of times available in day_data
        day_times = day_data['Horário'].tolist()
        print(f"Times available in day_data: {day_times}")



        # Iterate over the defined time slots to check availability
        for i in range(len(time_slots) - duration + 1):
            slot_is_available = True
            print(f"\nChecking slot starting at {time_slots[i]}:")

            Lorena_Counter = 0
            Luana_Counter = 0

            for j in range(duration):
                current_time = time_slots[i + j]

                # Only consider slots that exist in the day_data
                if current_time not in day_times:
                    print(f"  {current_time} not found in day_times.")
                    slot_is_available = False
                    break

                time_data = day_data[day_data['Horário'] == current_time]

                slot_is_available = True
                # Check if the slot is taken by Lorena
                lorena_taken = can_do in [1, 3] and len(str(time_data['Lorena'].values[0]).strip()) > 0
                print(f"Lorena taken: {lorena_taken}")
                if lorena_taken == True:
                    Lorena_Counter += 1
                    

                # Check if the slot is taken by Luana
                luana_taken = can_do in [2, 3] and len(str(time_data['Luana'].values[0]).strip()) > 0
                print(f"Luana taken: {luana_taken}")
                if luana_taken == True:
                    Luana_Counter += 1

                # Determine if the slot is available based on 'can_do'
                if (can_do == 1 and lorena_taken) or (can_do == 2 and luana_taken) or (can_do == 3 and (lorena_taken and luana_taken)):
                    slot_is_available = False
                    print(f"  Slot taken at {current_time}.")
                    break

            if (can_do == 3 and (Lorena_Counter > 0 and Luana_Counter > 0)):
                slot_is_available = False
                print(f' both counters bigger than 0: Lo: {Lorena_Counter} Lu: {Luana_Counter}')

            if slot_is_available:
                available_slots.append(time_slots[i].strftime("%H:%M"))
                print(f"  Slot {time_slots[i].strftime('%H:%M')} added as available.")

        print(f"Available time slots: {available_slots}")

        if not available_slots:
            return "Opa, desculpe😔 Não há horário disponível para este dia!"

        return available_slots
    except:
        return "Ops, não conseguimos encontrar esta data na nossa agenda 😔\nTem certeza de que esta data não está no passado ou existe? 😳"

def book_appointment(date_str, time_slot, procedure_name, name, wa_number):
    # Convert date string to identify the correct sheet
    date = datetime.strptime(date_str, "%Y/%m/%d")
    user_document = users.find_one({"number": wa_number}, {"selected_procedure": 1, "main_procedure": 1})
    main_procedure = user_document.get("main_procedure") if user_document else "x"
    main_procedure_list = (globals()[main_procedure])
    print(f"procedure: {main_procedure}: {procedure_name}") 
    duration = main_procedure_list[procedure_name]["duration"]
    time_slot = pd.to_datetime(time_slot, format="%H:%M").time()
    sheet_name = date.strftime("%Y-%m")
    

    date_object = datetime.strptime(date_str, "%Y/%m/%d")
                        # Format the date to the desired format
    formatted_date = date_object.strftime("%d %B %Y") 
                        # Replace the English month name with the Portuguese one
    formatted_date_portuguese = formatted_date.replace(date_object.strftime("%B"), month_translation[date_object.strftime("%B")]    )

    # Retrieve the sheet data
    sheet = read_sheet(file_id, sheet_name)

    # Convert 'Data' to datetime and 'Horário' to time
    sheet['Data'] = pd.to_datetime(sheet['Data'])
    sheet['Horário'] = pd.to_datetime(sheet['Horário'], format="%H:%M").dt.time

    # Debugging: Print the columns to see what data is present
    print(f"Contato Lo Column Data:\n{sheet['Contato Lo']}")
    print(f"Contato Lu Column Data:\n{sheet['Contato Lu']}")

    # Clean data: Remove whitespace, non-numeric characters, and ensure string type
    sheet['Contato Lo'] = (
        sheet['Contato Lo']
        .astype(str)
        .str.replace(r'\D+', '', regex=True)
        .str.strip()
    )
    sheet['Contato Lu'] = (
        sheet['Contato Lu']
        .astype(str)
        .str.replace(r'\D+', '', regex=True)
        .str.strip()
    )

    # Ensure 'number' is also treated as a string and clean it using regex
    number_1 = re.sub(r'\D+', '', str(wa_number).strip())
    number_2 = str(number_1).replace("@c.us", "")

    # Debugging: Check after cleaning
    print(f"Cleaned Contato Lo Column Data:\n{sheet['Contato Lo']}")
    print(f"Cleaned Contato Lu Column Data:\n{sheet['Contato Lu']}")
    print(f"Checking for number: {number_2}")

    # Count the occurrences of the contact number in both columns
    contato_count_lo = sheet['Contato Lo'].eq(number_2).sum()
    contato_count_lu = sheet['Contato Lu'].eq(number_2).sum()
    total_contato_count = contato_count_lo + contato_count_lu

    # Debugging prints
    print(f"Contato Lo counts: {contato_count_lo}, Contato Lu counts: {contato_count_lu}, Total: {total_contato_count}")

    # Check if the contact number has more than 3 appointments in the sheet
    if total_contato_count >= 3:
        return f"Desculpe {name}... 😵‍💫\nNosso sistema automatizado permite apenas 3 consultas por mês para o mesmo número de contato.\n\nA recepcionista entrará em contato com você caso queira fazer outro agendamento no mês de sua escolha! 🙂"

    

    # Filter the data for the specified date
    day_data = sheet[sheet['Data'] == pd.to_datetime(date_str)]
    print(f'DAY DATA:\n{day_data}')

    contato_count_lo_day = day_data['Contato Lo'].eq(number_2).sum()
    print(f"contato_count_lo_day = {contato_count_lo_day}")
    contato_count_lu_day = day_data['Contato Lu'].eq(number_2).sum()
    print(f"contato_count_lu_day = {contato_count_lu_day}")
    
    # Locate the row that matches the specific time slot
    time_row = day_data[day_data['Horário'] == time_slot]

    if not time_row.empty:
        # Check the `can_do` attribute for the procedure
        if procedure_name in main_procedure_list:
            can_do = main_procedure_list[procedure_name]["can_do"]

            if contato_count_lo_day > 0 and can_do == 3 :
                can_do = 1
                print("can do edited to 1")
            if contato_count_lu_day > 0 and can_do == 3 :
                can_do = 2
                print("can do edited to 2")


            # Open the Google Sheet using gspread
            gc = gspread.authorize(creds)
            gsheet = gc.open_by_key(file_id).worksheet(sheet_name)

            if can_do == 3:
                if len(str(time_row['Luana'].values[0])) == 0:
                    sufficient_space_counter = 0
                    for i in range(duration):
                        if gsheet.cell(time_row.index[0] + 2 + i, 5).value is None:
                            sufficient_space_counter += 1

                    if sufficient_space_counter == duration:
                        
                        # Update cells for Luana
                        gsheet.update_cell(time_row.index[0] + 2, 5, procedure_name)
                        for i in range((duration - 1)):
                            gsheet.update_cell(time_row.index[0] + 3 + i, 5, 'ocupado') 
                        gsheet.update_cell(time_row.index[0] + 2, 7, name)
                        gsheet.update_cell(time_row.index[0] + 2, 9, number_2)
                        gsheet.update_cell(time_row.index[0] + 2, 11, 'PREC. CONFIRM!')                            
                        return f"*{procedure_name}* agendada com sucesso! 😍\n\nEm: {formatted_date_portuguese} às {time_slot}\n\n\n{name}, sua vaga está reservada. A recepcionista entrará em contato com você para confirmar isso! 🙂\n\n_Observe que a política da nossa empresa exige um pagamento adiantado de 15% do valor total antes da confirmação definitiva._"
                    
                    elif len(str(time_row['Lorena'].values[0])) == 0:
                        gsheet.update_cell(time_row.index[0] + 2, 4, procedure_name)
                        for i in range((duration - 1)):
                            gsheet.update_cell(time_row.index[0] + 3 + i, 4, 'ocupado')
                        gsheet.update_cell(time_row.index[0] + 2, 6, name)
                        gsheet.update_cell(time_row.index[0] + 2, 8, number_2)
                        gsheet.update_cell(time_row.index[0] + 2, 10, 'PREC. CONFIRM!')                       
                        return f"*{procedure_name}* agendada com sucesso! 😍\n\nEm: {formatted_date_portuguese} às {time_slot}\n\n\n{name}, sua vaga está reservada. A recepcionista entrará em contato com você para confirmar isso! 🙂\n\n_Observe que a política da nossa empresa exige um pagamento adiantado de 15% do valor total antes da confirmação definitiva._"
                    else:
                        return "opa, deu bug🤯.\nPor favor, tente novamente."
                        
                elif len(str(time_row['Lorena'].values[0])) == 0:
                    gsheet.update_cell(time_row.index[0] + 2, 4, procedure_name)
                    for i in range((duration - 1)):
                        gsheet.update_cell(time_row.index[0] + 3 + i, 4, 'ocupado')
                    gsheet.update_cell(time_row.index[0] + 2, 6, name)
                    gsheet.update_cell(time_row.index[0] + 2, 8, number_2) 
                    gsheet.update_cell(time_row.index[0] + 2, 10, 'PREC. CONFIRM!')                    
                    return f"*{procedure_name}* agendada com sucesso! 😍\n\nEm: {formatted_date_portuguese} às {time_slot}\n\n\n{name}, sua vaga está reservada. A recepcionista entrará em contato com você para confirmar isso! 🙂\n\n_Observe que a política da nossa empresa exige um pagamento adiantado de 15% do valor total antes da confirmação definitiva._"
                else:
                    return "opa, deu bug🤯.\nPor favor, tente novamente."

            elif can_do == 1:
                if len(str(time_row['Lorena'].values[0])) == 0:
                    gsheet.update_cell(time_row.index[0] + 2, 4, procedure_name)
                    for i in range((duration - 1)):
                        gsheet.update_cell(time_row.index[0] + 3 + i, 4, 'ocupado')
                    gsheet.update_cell(time_row.index[0] + 2, 6, name)
                    gsheet.update_cell(time_row.index[0] + 2, 8, number_2)
                    gsheet.update_cell(time_row.index[0] + 2, 10, 'PREC. CONFIRM!')                        
                    return f"*{procedure_name}* agendada com sucesso! 😍\n\nEm: {formatted_date_portuguese} às {time_slot}\n\n\n{name}, sua vaga está reservada. A recepcionista entrará em contato com você para confirmar isso! 🙂\n\n_Observe que a política da nossa empresa exige um pagamento adiantado de 15% do valor total antes da confirmação definitiva._"
                else:
                    return "opa, deu bug🤯.\nPor favor, tente novamente."

            elif can_do == 2:
                if len(str(time_row['Luana'].values[0])) == 0:
                    gsheet.update_cell(time_row.index[0] + 2, 5, procedure_name)
                    for i in range((duration - 1)):
                        gsheet.update_cell(time_row.index[0] + 3 + i, 5, 'ocupado')
                    gsheet.update_cell(time_row.index[0] + 2, 7, name)
                    gsheet.update_cell(time_row.index[0] + 2, 9, number_2)
                    gsheet.update_cell(time_row.index[0] + 2, 11, 'PREC. CONFIRM!')                      
                    return f"*{procedure_name}* agendada com sucesso! 😍\n\nEm: {formatted_date_portuguese} às {time_slot}\n\n\n{name}, sua vaga está reservada. A recepcionista entrará em contato com você para confirmar isso! 🙂\n\n_Observe que a política da nossa empresa exige um pagamento adiantado de 15% do valor total antes da confirmação definitiva._"
                else:
                    return "opa, deu bug🤯.\nPor favor, tente novamente."
        else:
            return "Procedure not found."
    else:
        return "Time slot not found."

def product_menu(file_id_2, sheet_name="LCprodutos", description_mode=False, index=None):
    df = read_sheet(file_id_2, sheet_name)
    
    if isinstance(df, str):  # Error handling from read_sheet
        return df
    
    # Filter out items that are out of stock
    df_filtered = df[df['Em estoque?'].str.lower() == 'sim']

    if not description_mode:
        # Return a list of product names
        product_list = df_filtered['Produto'].tolist()
        return product_list
    else:
        if index is not None and 0 <= index < len(df_filtered):
            # Return the name, description, and price of the product at the given index as a list
            selected_product = df_filtered.iloc[index]
            return [
                f'*{selected_product["Produto"]}*',
                f'{selected_product["Descrição"]}',
                f'Valor do investimento R$: {selected_product["Preço"]}'
            ]
        else:
            return "Invalid index or out of range"


def order_notification(order_id):
        
        order = orders.find_one( {"_id": order_id})
    # Replace with your MongoDB connection string
        orders_list = []
         
        number = (str(order.get("number", ""))).replace("@c.us", "")  
        order_details = [
            (f'**************\n'),
            (f'NUMERO: {number}\n'),
            (f'DATA: {str(order.get("data", ""))}\n'),
            (f'NOME: {order.get("name", "")}\n'),
            (f'*PRODUTO*: {order.get("produto", "")}\n\n'),
            (f'*Info*:\n{order.get("info", "")}\n**************'),
                    
        ]
        orders_list.append(order_details)

        # Combine the list of lists into a single string
        combined_string = "\n\n".join(["".join(order) for order in orders_list])


        return combined_string

  
    # Function to reset inactive users
def reset_inactive_users():
        users.update_many(
            {"status": {"$ne": "main"}},  # Assuming you want to reset users who aren't already 'main'
            {"$set": {"status": "main"}}
        )
        print(f"Inactive users reset to main status. @ {datetime.now()}")


                


client = SocketClient('https://whatsappbotlcpgm-efc856ff6190.herokuapp.com/api-docs/', os.getenv("API_KEY"))

def messageHandler(message):
    if is_bot_active():
        ti.sleep(2)
        print(f"---------------RECEIVED MESSAGE!---------------")

        # Extract 'data' key from the outer dictionary
        if 'data' in message:
            data = message['data']
            text = data.get('body', '[No text]')
            wa_number = data.get('from', '[Unknown Number]')
            number = wa_number.replace("@c.us", "")

            if "g.us" in str(wa_number):
                print("Group chat message not responded")
                return "Group chat, no response"
                    
            blocked_numbers = get_all_blocked_numbers()
            print(f'Blocked numbers {blocked_numbers} ')

            users.update_one(
                {"number": wa_number},
                {"$set": {"last_active": datetime.now()}})


            try:
            # Try to get the user's name from the database
                user = users.find_one({"number": wa_number})
                name = user.get("name", "querida") if user else "querida"

            except Exception as e:
                logging.error(f"Error retrieving name: {e}")
                name = "querida"  # Default to "querida" if there's an error or no user            

            logging.debug(f"Received message: {text}")
            print(f"Received message: {text}")
            # Retrieve the user document, focusing only on the selected_procedure field
            user_document = users.find_one({"number": wa_number}, {"selected_procedure": 1, "main_procedure": 1})
            # Extract the selected_procedure value if it exists
            selected_procedure = user_document.get("selected_procedure") if user_document else "x"
            main_procedure = user_document.get("main_procedure") if user_document else "x"

            if not user: 
            # If user does not exist, ask for the user's name
            
            # Insert user with an empty name and status to be updated later
                users.insert_one({"number": wa_number, "status": "waiting_for_name", "messages": [], "name": ""})
                client.sendText(wa_number, "Olá, tudo bem? 😊\nNosso novo sistema automatizado ainda não registrou você!😬\nDesculpe pela inconveniência!🥺\n\nQual é seu nome?")   
            #WAITING FOR NAME    
            elif user['status'] == "waiting_for_name":
                # Validate the name to ensure it contains only letters
                if re.match("^[A-Za-z]+(?:\s[A-Za-z]+){0,2}$", text):  # Check if the name contains only letters and spaces
                    # If user provides a valid name, save the name and update status
                    users.update_one({"number": wa_number}, {"$set": {"name": text, "status": "main"}})
                    client.sendText(wa_number,f"Obrigada, {text}! Como podemos ajudá-lo hoje? 😊\n\nPara marcar um agendamento para um procedimento,\ndigite 1️⃣\n\nPara acessar nossos produtos,\ndigite 2️⃣\n\nPara outras perguntas ou comentários,\ndigite 3️⃣ \n\n\nGostaríamos de anunciar que recentemente também realizamos procedimentos de epilação a laser!🥳")
                    users.update_one({"number": wa_number}, {"$set": {"status": "phase initial"}})
                else:
                    # If the name is invalid, ask for the name again
                    client.sendText(wa_number,"Por favor insira um nome válido (apenas letras) 😳.")
            # MAIN STATUS
            elif user['status'] == "main":
                if wa_number not in blocked_numbers:
                # If the user exists and the name is known
                    print(f' number not blocked: {wa_number}')
                    client.sendText(wa_number,f"Oi {name}! Você está bem? Como podemos ajudá-lo? 🤗\n\nPara marcar um agendamento para um procedimento,\ndigite 1️⃣\n\nPara acessar nossos produtos,\ndigite 2️⃣\n\nPara falar conosco pessoalmente e perguntas/comentários\ndigite 3️⃣ \n\n\nGostaríamos de anunciar que recentemente também realizamos procedimentos de epilação a laser!🥳")
                    users.update_one({"number": wa_number}, {"$set": {"status": "phase initial"}})
                else:
                    client.sendText(wa_number,f"Oi {name}! 🙂\nNosso bot do WhatsApp não está funcionando no momento. \n\nA recepcionista tentará entrar em contato com você o mais breve possível!")
                    users.update_one({"number": wa_number}, {"$set": {"status": "being ghosted"}})
            #PHASE INITIAL 
            elif user['status'] == "phase initial":
                if text.lower() == "reset status":
                    update_last_human_message()
                    client.sendText(wa_number,f"All chats reset to main status!")
                    users.update_many(
                        {"status": {"$ne": "main"}},  # Assuming you want to reset users who aren't already 'main'
                        {"$set": {"status": "main"}} )
                elif text.lower() == "blacklist mode":
                    client.sendText(wa_number,f"Insira o número que deseja colocar na blacklist.\nVocê deve adicionar o código do país.\n\nExemplo: o número brasileiro 9185772657 \n(em alguns casos escrito como 91 98 5772657)\n\nprecisa ser escrito como +559185772657")
                    users.update_one({"number": wa_number}, {"$set": {"status": "blacklisting"}})  # Set status             
                elif text.lower() == "1":
                    procedure_list = "\n".join([f"{i}. *{procedure_name.replace('_', ' ')}*" for i, procedure_name in enumerate(procedures, start=1)])
                    # Handle ordering process
                    client.sendText(wa_number,f"Ótimo! 😁\n*Por favor, {name}, escolha a número do procedimento:*\n\n{procedure_list}\n\n\nObserve que para os seguintes tratamentos você precisa entrar em contato conosco pessoalmente:\n\n* Depilação a laser\n* Remoção de tatuagens, manchas ou sinais\n* Tratamento de acne ou melasma\n\n*Para voltar, digite* 0️⃣\n\n*Para entrar em contato conosco pessoalmente, digite* #️⃣")
                    users.update_one({"number": wa_number}, {"$set": {"status": "procediment phase"}})  # Set status 
                elif text.lower() == "2":
                    # Process the order
                    product_list = product_menu(file_id_2, sheet_name="LCprodutos", description_mode=False, index=None)
                    product_list_display = "\n".join([f"{i}. {item}" for i, item in enumerate(product_list, start=1)])
                    client.sendText(wa_number,f"Ótimo! Aqui está o menu:\n\n{product_list_display}\n\nPor favor, *digite o número do produto que você deseja pedir*.\n\n\n_O produto que você quer não está nesta lista?_\nEle possivelmente está fora de estoque.\nEm breve, repomos nosso estoque.\n\n*Para voltar, digite* 0️⃣")
                    users.update_one({"number": wa_number}, {"$set": {"status": "product phase"}})
                elif text.lower() == "3":
                    # Handle ordering process
                    client.sendText(wa_number,"Ótimo! Por favor, aguarde até que nossa recepcionista possa entrar em contato com você!\n\nInformamos que nosso horário de funcionamento é o seguinte:\n\nSegunda-feira: *Fechado*\nTerça-feira: *12:30-18:00*\nQuarta-feira: *12:30-18:00*\nQuinta-feira: *12:30-18:00*\nSexta-feira: *12:30-18:00*\nSábado: *8:00-18:00*\nDomingo: *Fechado*\n\n\n_Os horários de funcionamento podem ser diferentes durante os feriados!_\n\n*Você já pode deixar sua mensagem!*👇🏽😊")
                    users.update_one({"number": wa_number}, {"$set": {"status": "phase initial"}})  # Set status 
                else:
                    client.sendText(wa_number,"")

            elif user['status'] == "blacklisting":
                blocked_number = str(text) + '@c.us'
                blacklist.insert_one({"blocked_number": blocked_number})
                client.sendText(wa_number,f"{blocked_number} adicionada à blacklist. 📵👮🏾‍♂️")
                users.update_one({"number": wa_number}, {"$set": {"status": "main"}})

            elif user['status'] == "being ghosted":
                client.sendText(wa_number,"")
            
            elif user['status'] == "product phase":
                if text.lower() == "0":
                    # Process the order
                    client.sendText(wa_number,"Como podemos ajudá-lo? 🤗\n\nPara marcar um agendamento para um procedimento,\ndigite 1️⃣\n\nPara acessar nossos produtos,\ndigite 2️⃣\n\nPara outras perguntas ou comentários,\ndigite 3️⃣.")
                    users.update_one({"number": wa_number}, {"$set": {"status": "phase initial"}})    
                else:        
                    try:
                        product_index = int(text.strip()) - 1
                        product_list = product_menu(file_id_2, sheet_name="LCprodutos", description_mode=False, index=None)
                        if product_index < 0 or product_index >= len(product_list):
                            client.sendText(wa_number,"Número inválido. Por favor, escolha um produto válido.")
                        else:
                            product_list = product_menu(file_id_2, sheet_name="LCprodutos", description_mode=True, index=product_index)
                            print(f"LIST: {product_list}")
                            product_list_visual = "\n\n".join(product_list)
                            print(product_list_visual)
                            print(f"product selected: {product_list[0]}")
                            # Store the selected procedure in the user's record
                            users.update_one({"number": wa_number}, {"$set": {"selected_product": product_list[0]}})
                            # Prompt the user for a date
                            client.sendText(wa_number,f"{name} 🙂,\nvocê selecionou o seguinte produto:\n\n{product_list_visual}\n\nComentários e dúvidas podem ser feitos após o pedido!\n\nPara *fazer esse pedido*, digite 1️⃣\n\n Para *cancelar e voltar*, digite 0️⃣")      
                            # Update status to 'date phase'
                            users.update_one({"number": wa_number}, {"$set": {"status": "product phase 2"}})
                    except ValueError:
                        client.sendText(wa_number,"Por favor, insira um número válido.")
            
            elif user['status'] == "product phase 2":
                if text.lower() == "0":
                    # Process the order
                    client.sendText(wa_number,"Como podemos ajudá-lo? 🤗\n\nPara marcar um agendamento para um procedimento,\ndigite 1️⃣\n\nPara acessar nossos produtos,\ndigite 2️⃣\n\nPara outras perguntas ou comentários,\ndigite 3️⃣.")
                    users.update_one({"number": wa_number}, {"$set": {"status": "phase initial"}})
                elif text.lower() == "1":
                    # Process the order
                    date = datetime.now()
                    client.sendText(wa_number,f"\n\nÓtima escolha {name}! 😃\n\nEntraremos em contato com você o mais breve possível para continuar com seu pedido.🏃🏽‍♀️‍➡️\n\nPara facilitar o pedido, especifique já a forma de pagamento e forma de entrega (retirada ou entrega)!😊")
                    orders.insert_one({"number": wa_number, "data": date, "status": "não confirmado", "informações": text, "name": name, "produto": user.get("selected_product")})
                    users.update_one({"number": wa_number}, {"$set": {"status": "product phase 3"}})                
                else:    
                    client.sendText(wa_number,f"Por favor {name} 😳\nDigite um número valido, ou retorne digitando 0️⃣")

            elif user['status'] == "product phase 3":
                if text.lower() == "0":
                    # Process the order
                    client.sendText(wa_number,"Como podemos ajudá-lo? 🤗\n\nPara marcar um agendamento para um procedimento,\ndigite 1️⃣\n\nPara acessar nossos produtos,\ndigite 2️⃣\n\nPara outras perguntas ou comentários,\ndigite 3️⃣.")
                    users.update_one({"number": wa_number}, {"$set": {"status": "phase initial"}})
                else:
                    ti.sleep(5)
                    # Process the order
                    latest_order = orders.find_one(
                            {"number": wa_number}, 
                            sort=[("_id", -1)]  # Sort by _id in descending order to get the most recent document
                        )
                    if latest_order:
                        # Update the status of the most recent document
                        orders.update_one(
                            {"_id": latest_order["_id"]}, 
                            {"$set": {"status": "CONFIRMADO", "info": text}} )

                        client.sendText(wa_number,f"\n\n*Parabéns pelo seu pedido {name}!* 😍\n\nNossa recepcionista entrará em contato com você o mais rápido possível para confirmar!\n\n")
                        
                        order_id = latest_order.get("_id")
                        client.sendText(os.getenv("NUMBER_1"), f"NOVO PEDIDO FEITO NO NÚMERO DO LC!\n\n\n{order_notification(order_id)}")
                        client.sendText(os.getenv("NUMBER_2"), f"NOVO PEDIDO FEITO NO NÚMERO DO LC!\n\n\n{order_notification(order_id)}")
                        
                        
                        users.update_one({"number": wa_number}, {"$set": {"status": "phase initial"}})
                    else:            
                        client.sendText(wa_number,f"Desculpe {name} 😢\n\nNosso sistema de pedidos não funciona agora. Nossa recepcionista entrará em contato para fazer seu pedido manualmente!")
                        users.update_one({"number": wa_number}, {"$set": {"status": "main"}})
        
            #PROCEDIMENT PHASE
            elif user['status'] == "procediment phase":
                if text.lower() == "0":
                    # Process the order
                    client.sendText(wa_number,"Como podemos ajudá-lo? 🤗\n\nPara marcar um agendamento para um procedimento,\ndigite 1️⃣\n\nPara acessar nossos produtos,\ndigite 2️⃣\n\nPara outras perguntas ou comentários,\ndigite 3️⃣.")
                    users.update_one({"number": wa_number}, {"$set": {"status": "phase initial"}})
                elif text.lower() == "#":
                    # Process the order
                    client.sendText(wa_number,f"Ótimo! Por favor {name}, aguarde até que nossa recepcionista possa entrar em contato com você!\n\nInformamos que nosso horário de funcionamento é o seguinte:\n\nSegunda-feira: *Fechado*\nTerça-feira: *12:30-18:00*\nQuarta-feira: *12:30-18:00*\nQuinta-feira: *12:30-18:00*\nSexta-feira: *12:30-18:00*\nSábado: *8:00-18:00*\nDomingo: *Fechado*\n\n\n_Os horários de funcionamento podem ser diferentes durante os feriados!_")
                    users.update_one({"number": wa_number}, {"$set": {"status": "phase initial"}})  # Set status        
                else:        
                    try:
                        procedure_index = int(text.strip()) - 1
                        if procedure_index < 0 or procedure_index >= len(procedures):
                            client.sendText(wa_number,"Número inválido. Por favor, escolha um procedimento válido.")
                        else:

                            procedure_name_main = list(procedures.keys())[procedure_index]
                            # Store the selected procedure in the user's record
                            users.update_one({"number": wa_number}, {"$set": {"selected_procedure": procedure_name_main}})
                            # Prompt the user for a date
                            procedure_list = globals()[procedure_name_main]

                            new_procedure_list = "\n".join([f"{i}. {procedure_name}" for i, procedure_name in enumerate(procedure_list, start=1)])


                            client.sendText(wa_number,f"Você escolheu *{procedure_name_main.replace('_', ' ')}*.\n\n{new_procedure_list}\n\nPor favor digite o número do procedimento desejado 😊\n\nPara voltar, digite 0️⃣")

                            
    
                            # Update status to 'date phase'
                            users.update_one({"number": wa_number}, {"$set": {"status": f"{procedure_name_main} phase"}})
                    except ValueError:
                        client.sendText(wa_number,"Por favor, insira um número válido.")
            
            #SUB_PROCEDIMENT PHASE
            elif user['status'] == f"{selected_procedure} phase":
                if text.lower() == "0":               
                    procedure_list = "\n".join([f"{i}. {procedure_name.replace('_', ' ')}" for i, procedure_name in enumerate(procedures, start=1)])
                    client.sendText(wa_number,f"Por favor, {name}, escolha a procedimento:\n\n{procedure_list}\n\nPara voltar, digite 0️⃣.")
                    users.update_one({"number": wa_number}, {"$set": {"status": "procediment phase"}})    
                else:                        
                    try:
                        procedure_index = int(text.strip()) - 1
                        if procedure_index < 0 or procedure_index >= len(globals()[selected_procedure]):
                            client.sendText(wa_number,"Número inválido. Por favor, escolha um procedimento válido.")
                        else:
                            # Get the selected procedure name
                            procedure_name = list((globals()[selected_procedure]).keys())[procedure_index]
                            # Store the selected procedure in the user's record
                            users.update_one({"number": wa_number}, {"$set": {"selected_procedure": procedure_name}})
                            users.update_one({"number": wa_number}, {"$set": {"main_procedure": selected_procedure}})
                            # Prompt the user for a date
                            client.sendText(wa_number,f"Você escolheu *{procedure_name}*.\n\nPor favor {name}, *para continuar marcando uma consulta digite a data desejada*\n(*formato AAAA/MM/DD*)\n(Exemplo: 20 Dezembro 2024 será: 2024/12/20)\n\n_Para mais informação sobre o procedimento, e o Valor do investimento do procedimento, digite_ #️⃣\n\nPara voltar, digite 0️⃣")
                            # Update status to 'date phase'
                            users.update_one({"number": wa_number}, {"$set": {"status": "date phase"}})
                    except ValueError:
                        client.sendText(wa_number,"Por favor, insira um número válido.")
            
            
            #DATE PHASE
            elif user['status'] == "date phase":
                if text.lower() == "#":
                    procedure_name = user.get("selected_procedure")
                    main_procedure = user.get("main_procedure")
                    description = (globals()[main_procedure])[procedure_name]["description"]
                    client.sendText(wa_number,f"{description}\n\n\nPor favor, informe a data desejada (*formato AAAA/MM/DD*)\n\nPara voltar, digite 0️⃣")
                elif text.lower() == "0":
                    client.sendText(wa_number,"Como podemos ajudá-lo? 🤗\n\nPara marcar um agendamento para um procedimento,\ndigite 1️⃣\n\nPara acessar nossos produtos,\ndigite 2️⃣\n\nPara outras perguntas ou comentários,\ndigite 3️⃣.")
                    users.update_one({"number": wa_number}, {"$set": {"status": "phase initial"}})               
                        
                else:
                    date_str = text.strip()
                    if is_valid_date(date_str):
                        users.update_one({"number": wa_number}, {"$set": {"selected_date": date_str}})
                        procedure_name = user.get("selected_procedure")
                        main_procedure = user.get("main_procedure")
                        main_procedure_list = (globals()[main_procedure])
                        if procedure_name:
                            available_slots = get_available_times(
                                date_str, 
                                procedure_name, 
                                main_procedure_list[procedure_name]["can_do"], 
                                main_procedure_list[procedure_name]["duration"], 
                                file_id, number
                            )
                            indexed_time_slots = [f"{idx + 1}. {slot}" for idx, slot in enumerate(available_slots)]
                            # Convert the date string to a datetime object
                            date_object = datetime.strptime(date_str, "%Y/%m/%d")
                            # Format the date to the desired format
                            formatted_date = date_object.strftime("%d %B %Y") 
                            # Replace the English month name with the Portuguese one
                            formatted_date_portuguese = formatted_date.replace(
                                date_object.strftime("%B"), month_translation[date_object.strftime("%B")])  
                            users.update_one({"number": wa_number}, {"$set": {"readable_date": formatted_date_portuguese}})                      
                                                
                            if isinstance(available_slots, list) and available_slots:
                                client.sendText(wa_number,
                                    f"Horários disponíveis\n\n *{formatted_date_portuguese}*\n" +
                                    "\n".join(indexed_time_slots) + 
                                    "\n\nPor favor, escolha o horário desejado digitando o número correspondente.\n\nPara voltar, digite 0️⃣"
                                )

                                users.update_one(
                                    {"number": wa_number},
                                    {"$set": {"status": "time phase", "selected_date": date_str}}
                                )
                            else:
                                client.sendText(wa_number,f"{available_slots}\n\nPor favor, informe uma outra data desejada (formato AAAA/MM/DD)\n\nPara voltar, digite 0️⃣")
                        else:
                            client.sendText(wa_number,"Ocorreu um erro ao tentar recuperar o procedimento selecionado. Por favor, tente novamente.")
                    else:
                        client.sendText(wa_number,"Formato de data inválido. Por favor, use o formato AAAA/MM/DD.")

            # TIME PHASE
            elif user['status'] == "time phase":
                if text.lower() == "0":
                    procedure_name = user.get("selected_procedure")
                    # Handle ordering process
                    client.sendText(wa_number,f"Você escolheu {procedure_name}. Por favor, informe a data desejada (formato AAAA/MM/DD).\n\nPara mais informação sobre o procedimento, e o Valor do investimento do procedimento, digite #️⃣\n\nPara voltar, digite 0️⃣")
                    users.update_one({"number": wa_number}, {"$set": {"status": "date phase"}})  # Set status
                else:
                    readable_date = user.get("readable_date")
                    main_procedure = user.get("main_procedure")
                    main_procedure_list = (globals()[main_procedure])
                    procedure_name = user.get("selected_procedure")
                    # Ensure that text is a number for selecting a time slot
                    if text.isdigit():
                        time_slot_index = int(text.strip()) - 1
                        available_slots = get_available_times(user.get("selected_date"), procedure_name, main_procedure_list[procedure_name]["can_do"], main_procedure_list[procedure_name]["duration"], file_id, number)
                        
                        if time_slot_index < 0 or time_slot_index >= len(available_slots):
                            client.sendText(wa_number,"Número inválido. Por favor, escolha um horário válido.")
                        else:
                            # date_str, procedure_name, can_do, time_slot, file_id
                            time_slot = available_slots[time_slot_index]
                            users.update_one({"number": wa_number}, {"$set": {"selected_time": time_slot}})
                            print(f"TIME SLOT SELECTED: {time_slot}")
                            client.sendText(wa_number,f"Você escolheu: {selected_procedure}\n\nO horário selecionado é: {time_slot}\nDia: *{readable_date}*\n\nPara confirmar sua reserva, digite 1️⃣\nPara cancelar e voltar, digite 0️⃣")
                            users.update_one({"number": wa_number}, {"$set": {"status": "time phase 2"}}) 
                    else:
                        client.sendText(wa_number,"Por favor, insira um número válido para selecionar o horário. 😁")
            elif user['status'] == "time phase 2":
                if text.lower() == "0":
                    procedure_name = user.get("selected_procedure")
                    # Handle ordering process
                    client.sendText(wa_number,f"Você escolheu *{procedure_name}*. Por favor, informe a data desejada (formato AAAA/MM/DD).\n\nPara mais informação sobre o procedimento, e o Valor do investimento do procedimento, digite #️⃣\n\nPara voltar, digite 0️⃣")
                    users.update_one({"number": wa_number}, {"$set": {"status": "date phase"}})  # Set status
                elif text.lower() == "1":
                    time_slot = user.get("selected_time")
                    main_procedure = user.get("main_procedure")
                    main_procedure_list = (globals()[main_procedure])
                    procedure_name = user.get("selected_procedure")
                    # Ensure that text is a number for selecting a time slot
                    if text.isdigit():
                        available_slots = get_available_times(user.get("selected_date"), procedure_name, main_procedure_list[procedure_name]["can_do"], main_procedure_list[procedure_name]["duration"], file_id, number)

                        print(f"TIME SLOT SELECTED: {time_slot}")
                        result = book_appointment(user.get("selected_date"), time_slot, procedure_name, name, wa_number)
                        client.sendText(wa_number, result)
                        users.update_one({"number": wa_number}, {"$set": {"status": "main"}})  # Reset status
                    else:
                        client.sendText(wa_number,"Por favor, insira um número válido para selecionar o horário. 😁")
        else:
            print("No 'data' field found in the message.")



async def main():
    # Sync request to get the host number
    print(client.getHostNumber())
    loaded_messages = int(client.getAmountOfLoadedMessages())
    counter = 0
    while loaded_messages > 100 and counter < 50:
        client.cutMsgCache()
        client.cutChatCache()
        counter += 1
    
    # Set up the scheduler
    scheduler = BackgroundScheduler()

        # Periodic cleanup of old jobs (this clears old jobs that might build up)
    def clear_old_jobs():
            print(f"Clearing old jobs. @ {datetime.now()}")
            scheduler.remove_all_jobs()

    def collect_garbage():
        print(f"Running garbage collection. @ {datetime.now()}")
        gc.collect()  # Manually trigger the garbage collector
        try:
            loaded_messages = int(client.getAmountOfLoadedMessages())
            if loaded_messages > 50:
                client.cutMsgCache()
                client.cutChatCache()
        except:
            print(f"msg cache not cleared")
        print(f"Garbage collection completed. @ {datetime.now()}")
    

    # Add jobs to the scheduler
    scheduler.add_job(reset_inactive_users, 'cron', hour=5, minute=0)
    scheduler.add_job(clear_old_jobs, 'interval', hours=3)  # Clear old jobs every 3 hours
    scheduler.add_job(collect_garbage, 'interval', hours=1)  # Run garbage collection every hour

    scheduler.start()  # Start the scheduler

    initialize_bot_status()  # Initialize the bot status

    # Listening for incoming messages
    client.onMessage(messageHandler)

    print("Waiting for messages...")

    # Keep the script running indefinitely
    while True:
        await asyncio.sleep(2)  # Non-blocking sleep to keep the loop alive

if __name__ == "__main__":
    try:
        # Run the async main loop
        asyncio.run(main())
    finally:
        # Ensure the socket disconnects properly on exit
        client.disconnect()
