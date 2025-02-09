import yaml
import re
import random
import smtplib
import datetime
import pytz
import time
import socket
import sys
import getopt
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

help_message = '''
To use, fill out config.yml with your own participants. You can also specify
DONT-PAIR so that people don't get assigned their significant other.

You'll also need to specify your mail server settings. An example is provided
for routing mail through gmail.

For more information, see README.
'''

REQRD = (
	'SMTP_SERVER',
	'SMTP_PORT',
	'USERNAME',
	'PASSWORD',
	'TIMEZONE',
	'PARTICIPANTS',
	'DONT-PAIR',
	'FROM',
	'SUBJECT',
	'MESSAGE-TEXT',
)

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.yml')


class Person:
	def __init__(self, name, email, invalid_matches):
		self.name = name
		self.email = email
		self.invalid_matches = invalid_matches

	def __str__(self):
		return "%s <%s>" % (self.name, self.email)


class Pair:
	def __init__(self, giver, reciever):
		self.giver = giver
		self.reciever = reciever

	def __str__(self):
		return "%s ---> %s" % (self.giver.name, self.reciever.name)


def parse_yaml(yaml_path=CONFIG_PATH):
	with open(yaml_path, 'r') as file:
		return yaml.safe_load(file)


def choose_reciever(giver, recievers):
	choice = random.choice(recievers)
	if choice.name in giver.invalid_matches or giver.name == choice.name:
		if len(recievers) == 1:
			raise Exception('Only one reciever left, try again')
		return choose_reciever(giver, recievers)
	else:
		return choice


def create_pairs(g, r):
	givers = g[:]
	recievers = r[:]
	pairs = []
	for giver in givers:
		try:
			reciever = choose_reciever(giver, recievers)
			recievers.remove(reciever)
			pairs.append(Pair(giver, reciever))
		except:
			return create_pairs(g, r)
	return pairs


class Usage(Exception):
	def __init__(self, msg):
		self.msg = msg


def main(argv=None):
	if argv is None:
		argv = sys.argv
	try:
		try:
			opts, args = getopt.getopt(argv[1:], "shc", ["send", "help"])
		except getopt.error as msg:
			raise Usage(msg)

		# option processing
		send = False
		for option, value in opts:
			if option in ("-s", "--send"):
				send = True
			if option in ("-h", "--help"):
				raise Usage(help_message)

		config = parse_yaml()
		for key in REQRD:
			if key not in config.keys():
				raise Exception(
					'Required parameter %s not in yaml config file!' % (key,))
		if len(config['MESSAGE-HTML']) > 0:
			with open('html_head.html', 'r') as html_head:
				html_header = html_head.read()
		participants = config['PARTICIPANTS']
		dont_pair = config['DONT-PAIR']
		if len(participants) < 2:
			raise Exception('Not enough participants specified.')

		givers = []
		for person in participants:
			name, email = re.match(r'([^<]*)<([^>]*)>', person).groups()
			name = name.strip()
			invalid_matches = []
			for pair in dont_pair:
				names = [n.strip() for n in pair.split(',')]
				if name in names:
					# is part of this pair
					for member in names:
						if name != member:
							invalid_matches.append(member)
			person = Person(name, email, invalid_matches)
			givers.append(person)

		recievers = givers[:]
		pairs = create_pairs(givers, recievers)
		if not send:
			print("""
Test pairings:

%s

To send out emails with new pairings,
call with the --send argument:

	$ python secret_santa.py --send

			""" % ("\n".join([str(p) for p in pairs])))

		if send:
			server = smtplib.SMTP(config['SMTP_SERVER'], config['SMTP_PORT'])
			server.starttls()
			server.login(config['USERNAME'], config['PASSWORD'])
		for pair in pairs:
			msg = MIMEMultipart('alternative')
			msg['Subject'] = config['SUBJECT'].format(
				santa=pair.giver.name, santee=pair.reciever.name)
			msg['From'] = config['FROM']
			msg['To'] = pair.giver.email
			text = config['MESSAGE-TEXT'] % (pair.giver.name, pair.reciever.name)
			msg.attach(MIMEText(text, 'plain'))
			if len(config['MESSAGE-HTML']) > 0:
				html = html_header + (config['MESSAGE-HTML'] % (pair.giver.name, pair.reciever.name))
				msg.attach(MIMEText(html, 'html'))
			if send:
				result = server.sendmail(
					msg['From'], [msg['To']], msg.as_string())
				print("Emailed %s <%s>" % (pair.giver.name, msg['To']))
		if send:
			server.quit()

	except Usage as err:
		print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
		print >> sys.stderr, "\t for help use --help"
		return 2


if __name__ == "__main__":
	sys.exit(main())
