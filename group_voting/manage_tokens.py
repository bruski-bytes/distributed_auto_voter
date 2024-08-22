#import boto3
from jose import jwt
import requests

ostracized_accounts = set()
living_payers = set()
# READ IN ALL TOKENS
all_tokens = []

# Clean login_results.txt

bad_email = set()
bad_pws = set()
success = set()

with open(f"login_results.txt", "r") as f:
    lines = f.readlines()
    for line in lines:
        line = line.strip("\n")
        parts = line.split(", ")
        print("parts: ", parts)
        if parts[1] == "success":
            success.add(parts[0])
            all_tokens.append(parts[-1])
        elif parts[1] == "bad email":
            bad_email.add(parts[0])
        else:
            bad_pws.add(parts[0])

       

with open("updated_login_results.txt", "w") as f:
    f.write("SUCCESSFULL ACCOUNTS\n")
    for s in success:
        f.write(s + "\n")
    f.write("BAD EMAILS\n")
    for b in bad_email:
        f.write(b + "\n")
    f.write("BAD PW\n")
    for b in bad_pws - success:
        f.write(b + "\n")

# with open(f"tokens.txt", "r") as f:
#     lines = f.readlines()
#     for line in lines:
#         line = line.strip("\n")
#         if len(line) > 0:
#             all_tokens.append(line)

with open(f"renewed_tokens.txt", "r") as f:
    lines = f.readlines()
    for line in lines:
        line = line.strip("\n")
        if len(line) > 0:
            all_tokens.append(line)

# with open(f"cred_tokens.txt", "r") as f:
#     lines = f.readlines()
#     for line in lines:
#         line = line.strip("\n")
#         parts = line.split(",")
#         all_tokens.append(parts[1])

# for instance_id in ['a', 'b', 'c']:
#     with open(f"cred_tokens_{instance_id}.txt", "r") as f:
#         lines = f.readlines()
#         for line in lines:
#             line = line.strip("\n")
#             parts = line.split(",")
#             all_tokens.append(parts[1])

print("All tokens: ",all_tokens)

# Get list of all ostracized players
url = "https://irk0p9p6ig.execute-api.us-east-1.amazonaws.com/prod/ostracizedPlayers"
response = requests.get(url)
jsonData = response.json()
ostracized_players = []

for player in jsonData['players']:
    ostracized_players.append(player['username'])

username_tokens = {}
with open('cleaned_latest_tokens.txt', 'w') as f:
    for t in all_tokens:
        decoded_token = jwt.decode(t, key=None, options={"verify_signature":False})
        if decoded_token['username'] not in ostracized_players:
            if decoded_token['username'] in username_tokens:
                # print("DUPLICATE")
                redecoded_token = jwt.decode(username_tokens[decoded_token['username']], key=None, options={"verify_signature":False})
                if decoded_token['iat'] > redecoded_token['iat']:
                    username_tokens[decoded_token['username']] = t
            else:
                username_tokens[decoded_token['username']] = t
                living_payers.add(decoded_token['username'])
                print(decoded_token)
        else:
            print("OSTRACIZED PLAYER: ", decoded_token['username'])
            ostracized_accounts.add(decoded_token['username'])
    
    for k, v in username_tokens.items():
        f.write(k + "," + v + '\n')
    
    print("LIVING PLAYERS: ", len(living_payers))
    print("OSTRACIZED PLAYERS: ", len(ostracized_accounts))
    print(ostracized_accounts)

# dynamodb = boto3.resource('dynamodb')


# accounts_table = dynamodb.create_table(
#     TableName='accounts',
#     KeySchema=[
#         {
#             'AttributeName': 'venmo_username',
#             'KeyType': 'HASH'  # Partition key
#         }
#     ],
#     AttributeDefinitions=[
#         {
#             'AttributeName': 'token',
#             'AttributeType': 'S'
#         },
#         {
#             'AttributeName': 'reserve',
#             'AttributeType': 'BOOL'
#         },
#         {
#             'AttributeName': 'instance_assignment',
#             'AttributeType': 'S'
#         },
#         {
#             'AttributeName': 'venmo_username',
#             'AttributeType': 'S'
#         }
#     ],
#     ProvisionedThroughput={
#         'ReadCapacityUnits': 1,
#         'WriteCapacityUnits': 1
#     }
# )

# print(accounts_table)
