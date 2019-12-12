from selenium import webdriver
from selenium.webdriver.support.ui import Select
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np

url_home = "http://sistemas.macae.rj.gov.br/transparencia/index.asp?acao=3&item=10"


def set_initial_page(year, initial_date, final_date, driver):

    # Set year field
    cmbAno_field = Select(driver.find_element_by_id('cmbAno'))
    cmbAno_field.select_by_visible_text(year)

    # Set Initial_date
    initial_date_field = driver.find_element_by_id('txtDataInicial')
    initial_date_field.clear()
    initial_date_field.send_keys(initial_date)

    # set final_date
    initial_date_field = driver.find_element_by_id('txtDataFinal')
    initial_date_field.clear()
    initial_date_field.send_keys(final_date)

    # confirm
    gerar_buton = driver.find_element_by_id('confirma')
    gerar_buton.click()
    return


def goto_companies_documents(company_name):
    driver.find_element_by_link_text(company_name).click()
    return


def download_tabela_empenho(driver, year):

    page = BeautifulSoup(driver.page_source, 'lxml')
    table = page.find('table', id='tbTabela')
    try:
        tabela_credores = pd.read_csv('credores_'+str(year)+'.csv')
        tabela_credores_site = pd.read_html(str(table), header=1)[0]
        tabela_credores_site['ano'] = year
        tabela_credores_site['download_status'] = 0
        tabela_credores_site = tabela_credores_site[~tabela_credores_site.Nome.isin(tabela_credores.Nome)]
        tabela_credores = tabela_credores.append(tabela_credores_site, sort=True)
        tabela_credores.to_csv('credores_'+str(year)+'.csv')
    except:
        tabela_credores = pd.read_html(str(table), header=1)[0]
        tabela_credores['ano'] = year
        tabela_credores['download_status'] = 0
        tabela_credores.to_csv('credores_'+str(year)+'.csv')

    credores = tabela_credores[tabela_credores.download_status==0].Nome

    for i, credor in enumerate(credores):
        goto_companies_documents(credor)
        page_empenhos = BeautifulSoup(driver.page_source, 'lxml')
        try:
            table_empenhos = page_empenhos.find('table', id='tbTabela1')
            empenho_df = pd.read_html(str(table_empenhos), header=1, skiprows=1, converters={'Número do Empenho': str})
        except:
            try:
                table_empenhos = page_empenhos.find('table', id='tbTabela2')
                empenho_df = pd.read_html(str(table_empenhos), header=1, converters={'Número do Empenho': str})
            except:
                driver.find_element_by_xpath('//*[@id="tbAtualizacao"]/tbody/tr[2]/td/input[1]').click()
                continue
        empenho_df = empenho_df[0]
        empenho_df = empenho_df[:-1]  # remove a ultima linha com totais

        numeros_empenhos = empenho_df['Número do Empenho']

        lista_detalhe_empenho = []

        for empenho in numeros_empenhos:
            goto_companies_documents(empenho)
            page_detalhe_empenho = BeautifulSoup(driver.page_source, 'lxml')
            table_det_empenho = page_detalhe_empenho.find('table', id='tbEmpenho')
            lista_detalhe_empenho.append(table_det_empenho)
            driver.find_element_by_xpath('//*[@id="tbAtualizacao"]/tbody/tr[2]/td/input[1]').click()

        driver.find_element_by_xpath('//*[@id="tbAtualizacao"]/tbody/tr[2]/td/input[1]').click()
        empenho_df['detalhe_empenho'] = lista_detalhe_empenho
        if i == 0:
            export_df = empenho_df
        else:
            export_df = export_df.append(empenho_df, sort=True)
        tabela_credores['download_status'] = np.where((tabela_credores.Nome==credor),1,tabela_credores.download_status)
        tabela_credores.to_csv('credores_' + str(year) + '.csv')

        # exportando tabela com os empenhos
        try:
            export_df_local = pd.read_csv('credores_empenhos_' + str(year) + '.csv')
            export_df_local = export_df_local.append(export_df, sort=True)
            export_df_local.to_csv('credores_empenhos_' + str(year) + '.csv')
        except:
            export_df.to_csv('credores_empenhos_' + str(year) + '.csv')

    return


def main(url):
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    driver = webdriver.Chrome(options=options)

    # Open Chrome
    driver.get(url)

    # Set initial Page information
    set_initial_page(year, initial_date, final_date, driver)

    try:
        download_tabela_empenho(driver, year)
        goto_companies_documents('Próxima página')
    except:
        print('Não existem mais empenhos.')
        continue

    # Close Chrome
    driver.close()

    return


if __name__ == "__main__":
    # year = ["2015", "2014", "2013", "2012", "2011", "2010", "2018", "2017", "2016"]
    year = '2015'
    initial_date = '01/01/2015'
    final_date = '31/03/2015'
    url = url_home

    for i in year:
        initial_date = '01/01/'+str(i)
        final_date = '31/12/'+str(i)
        main(url)
