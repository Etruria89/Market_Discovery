"""
This script includes utility functions
used to facilitate the stock market
analysis.

"""

import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def mail_sender(email_txt, data_send_db):
    """
    Mail sender function.

    This function is defined for sending
    the users an email with the report of the
    stock market analysis

    Args:
        email_txt = (str) filename of the file containing the sender email, its password and the receivers emails
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
    # message = tabulate([table[stk].values() for stk in table], headers = ['Symbol', 'Name', 'What To Do'])
    message = data_send_db
    msg.attach(MIMEText(message))

    mailserver = smtplib.SMTP('smtp.gmail.com', 587)
    # identify ourselves to smtp gmail client
    mailserver.ehlo()
    # secure our email with tls encryption
    mailserver.starttls()
    # re-identify ourselves as an encrypted connection
    mailserver.ehlo()
    mailserver.login(from_info, from_pwd)

    for names in to_names:
        mailserver.sendmail(from_name, names, data_send_db)

    mailserver.quit()