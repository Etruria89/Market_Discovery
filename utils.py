"""
This script includes utility functions
used to facilitate the stock market
analysis.

"""

import smtplib
import os
import csv
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def mail_sender(email_txt, text_send_db, date):
    """
    Mail sender function.

    This function is defined for sending
    the users an email with the report of the
    stock market analysis

    Args:
        email_txt = (str) filename of the file containing the sender email, its password and the receivers emails
        text_send_db = ()
        date = (str) containing the string of the today date to send fancy emails
    Return:
        Mail in inboxes of receivers

    """

    # read current working directory
    cwd = os.getcwd()

    # read email information
    file_path = cwd + '\\' + email_txt

    with open(file_path, 'r') as file:
        # Read the file line by line
        data_str = file.readlines()
        # Look for the string where you can get the relevant info
        from_ph = "From:"
        pwd_ph = "Pwd:"
        to_ph = "To:"
        iterable = iter(data_str)
        for line in iterable:
            if line.__contains__(from_ph):
                from_name = line.replace(from_ph, "").replace(" ", "")
                from_name = from_name[:-1]
            elif line.__contains__(pwd_ph):
                from_pwd = line.replace(pwd_ph, "").replace(" ", "")
                from_pwd = from_pwd[:-1]
            elif line.__contains__(to_ph):
                to_names = line.replace(to_ph, "").replace(" ", "")
                to_names = to_names.split(",")

        # Email generation
    msg = MIMEMultipart()
    from_info = from_name
    pwd = from_pwd
    msg['From'] = from_name
    msg['To'] = to_names
    msg['Subject'] = 'simple email in python'


    mailserver = smtplib.SMTP('smtp.gmail.com', 587)
    # identify ourselves to smtp gmail client
    mailserver.ehlo()
    # secure our email with tls encryption
    mailserver.starttls()
    # re-identify ourselves as an encrypted connection
    mailserver.ehlo()
    mailserver.login(from_info, from_pwd)

    for names in to_names:

        msg = text_send_db
        from_ = from_name
        to_ = names
        subject = '\U0001F680 Market Report: ' + date
        fmt = 'From: {}\r\nTo: {}\r\nSubject: {}\r\n{}'

        mailserver.sendmail(to_, from_, fmt.format(to_, from_, subject, msg).encode('utf-8'))

    mailserver.quit()


def read_csv_input(txt_file):
    """
    Read csv function function.

    This function reads a csv file
    and returns the list with the read values
    (generally used for th input)

    Args:
        email_txt = (str) name of the csv file to read
    Return:
        Mail in inboxes of receivers

    """


    with open(txt_file) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        output_list = []

        for row in csv_reader:
            for x in row:
                output_list.append(float(x))

    return output_list