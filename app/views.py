from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import pandas as pd
import psycopg2
from psycopg2 import sql
import requests

def sync_salesforce_data(request):
    if request.method == 'GET':
        # Salesforce credentials
        username = "sireesha.rtestapp@totalitglobal.com"
        password = "Testapp@23"
        security_token = "Hgb1cUV5LIwUIcg7sTlOOyZed"
        domain = "login"

        # Salesforce login endpoint
        login_url = f"https://{domain}.salesforce.com/services/oauth2/token"

        # Salesforce REST API endpoint for SOQL query
        query_url = "https://yourinstance.salesforce.com/services/data/vXX.X/query/"

        # Salesforce OAuth2 parameters
        params = {
            "grant_type": "password",
            "client_id": "your_client_id",
            "client_secret": "your_client_secret",
            "username": username,
            "password": password + security_token
        }

        try:
            # Perform OAuth2 login to obtain access token
            response = requests.post(login_url, params=params)
            access_token = response.json().get("access_token")

            # Salesforce SOQL query
            soql_query = """
                SELECT Project_Site__r.Country1__c,
                       Project_Site__r.City__c,
                       Project__r.Name AS projectname,
                       Skill_Level__c,
                       CurrencyIsoCode,
                       Project__c,
                       Purchase_Order__r.Customer__r.Name AS Customername,
                       Vendor_Project__r.Name AS vendorproject,
                       Vendor__r.Name AS vendorName,
                       MIN(Monthly_Rate__c) AS minMonthRate,
                       MAX(Monthly_Rate__c) AS maxMonthRate,
                       MIN(Vendor_Monthly_Rate__c) AS minVendorRate,
                       MAX(Vendor_Monthly_Rate__c) AS maxVendorRate,
                       AVG(Monthly_Rate__c) AS avgMonthlyRate,
                       AVG(Vendor_Monthly_Rate__c) AS avgVendorRate
                FROM Project_Services__c
                WHERE RecordType.Name = 'FTE'
                    AND Service_End_Date__c >= TODAY
                GROUP BY Project_Site__r.Country1__c, Project_Site__r.City__c, Vendor__r.Name, Project__r.Name, Purchase_Order__r.Customer__r.Name, Vendor_Project__r.Name, Skill_Level__c, CurrencyIsoCode, Project__c
            """

            # Prepare and send request to Salesforce REST API
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            query_params = {
                "q": soql_query
            }
            response = requests.get(query_url, headers=headers, params=query_params)

            # Convert response to DataFrame
            if response.status_code == 200:
                records = response.json().get("records", [])
                df = pd.DataFrame(records)

                # Database connection parameters
                dbname = 'test_db'
                user = 'postgres_db'
                password = 'Tig@1234'
                host = 'localhost'
                port = '5432'

                # Connect to PostgreSQL database
                conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host, port=port)
                cursor = conn.cursor()

                # Create table if not exists
                create_table_query = """
                    CREATE TABLE IF NOT EXISTS new_data (
                        Country1__c TEXT,
                        City__c TEXT,
                        projectname TEXT,
                        Skill_Level__c TEXT,
                        CurrencyIsoCode TEXT,
                        Project__c TEXT,
                        Customername TEXT,
                        vendorproject TEXT,
                        vendorName TEXT,
                        minMonthRate NUMERIC,
                        maxMonthRate NUMERIC,
                        minVendorRate NUMERIC,
                        maxVendorRate NUMERIC,
                        avgMonthlyRate NUMERIC,
                        avgVendorRate NUMERIC
                    )
                """
                cursor.execute(create_table_query)

                # Insert or update data into PostgreSQL table
                for index, row in df.iterrows():
                    # Define UPSERT query using psycopg2's sql module
                    upsert_query = sql.SQL("""
                        INSERT INTO new_data (
                            Country1__c, City__c, projectname, Skill_Level__c, CurrencyIsoCode,
                            Project__c, Customername, vendorproject, vendorName,
                            minMonthRate, maxMonthRate, minVendorRate, maxVendorRate,
                            avgMonthlyRate, avgVendorRate
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (projectname) DO UPDATE SET
                            Country1__c = EXCLUDED.Country1__c,
                            City__c = EXCLUDED.City__c,
                            Skill_Level__c = EXCLUDED.Skill_Level__c,
                            CurrencyIsoCode = EXCLUDED.CurrencyIsoCode,
                            Project__c = EXCLUDED.Project__c,
                            Customername = EXCLUDED.Customername,
                            vendorproject = EXCLUDED.vendorproject,
                            vendorName = EXCLUDED.vendorName,
                            minMonthRate = EXCLUDED.minMonthRate,
                            maxMonthRate = EXCLUDED.maxMonthRate,
                            minVendorRate = EXCLUDED.minVendorRate,
                            maxVendorRate = EXCLUDED.maxVendorRate,
                            avgMonthlyRate = EXCLUDED.avgMonthlyRate,
                            avgVendorRate = EXCLUDED.avgVendorRate
                    """)
                    # Execute UPSERT query with row values
                    cursor.execute(upsert_query, tuple(row))

                # Commit changes and close connection
                conn.commit()
                cursor.close()
                conn.close()

                return JsonResponse({'status': 'success', 'message': 'Salesforce data synchronized successfully'}, status=200)
            else:
                return JsonResponse({'status': 'error', 'message': f'Failed to retrieve data from Salesforce: {response.text}'}, status=500)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'An error occurred: {str(e)}'}, status=500)
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


from django.http import JsonResponse
from .utils import sync_salesforce_data

@require_http_methods(["POST"])
def trigger_sync(request):
    if request.method == 'POST':
        # Trigger Salesforce data synchronization
        response = sync_salesforce_data(request)
        return response
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)
