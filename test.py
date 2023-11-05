import common_tools

test = """A wait of 612 seconds is required before sending another message in this chat"""

print(common_tools.parse_digits(test.split("of ")[1].split("seconds")[0]))