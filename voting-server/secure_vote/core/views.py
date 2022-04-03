from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout

import json
import requests
import random
from hashlib import sha256

from .models import  Constituency,RegisteredVoters, UniqueID


# ------------Initializing blockchain-----------------------

# blockchain = Blockchain()

# blockchain.create_genesis_block()

# candidates = Party.objects.all()
# candidates = list(candidates)
# blockchain.create_candidates(candidates)

BLOCKCHAIN_NODE_ADDRESS = "http://127.0.0.1:5000"


# ------------Registration And Login-----------------------

def send_otp(phone, otp):
    print(f"phone = {phone} and otp = {otp}")


def register_page(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        age = request.POST.get('age')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        try:
            unique_id_details = UniqueID.objects.get(unique_id=username)
        except:
            messages.error(request, 'Unique id doesnot exists')
            return redirect('register')

        if username != unique_id_details.unique_id:
            messages.error(request, 'Unique id is invalid')
            return redirect('register')

        if email != unique_id_details.email:
            messages.error(request, 'email does not match unique id email')
            return redirect('register')

        if phone != unique_id_details.phone:
            messages.error(request, 'phone no does not match unique id email')
            return redirect('register')

        if int(age) < 18 or int(unique_id_details.age) < 18:
            messages.error(request, 'You must be 18+ to vote')
            return redirect('register')

        if int(age) != int(unique_id_details.age):
            messages.error(request, 'Age does not match with unique_id age')
            return redirect('register')

        if password != password2:
            messages.error(request, 'Passwords do not match')
            return redirect('register')

        if RegisteredVoters.objects.filter(username=username).exists():
            messages.error(request, 'Voter already registered')
            return redirect('register')

        if RegisteredVoters.objects.filter(email=email).exists():
            messages.error(request, 'That email is already registered')
            return redirect('register')

        if RegisteredVoters.objects.filter(phone=phone).exists():
            messages.error(request, 'That phone no is already registered')
            return redirect('register')

        try:
            otp = str(random.randint(100000, 999999))
            print("cid:  ", unique_id_details.c_id)
            user = RegisteredVoters.objects.create_user(username=username, 
                                                        name=name, 
                                                        email=email, 
                                                        phone=phone, 
                                                        age=age, 
                                                        password=password, 
                                                        otp=otp, 
                                                        c_id=unique_id_details.c_id)
            user.save()
            send_otp(phone, otp)
            request.session['phone'] = phone
            messages.success(request, 'Please verify OTP to complete registration')
            return redirect('register_otp')
        except: 
            messages.error(request, 'error while registering')
            return redirect('register')
    else:
        return render(request, 'register.html')


def register_otp(request):
    phone = request.session['phone']
    if request.method == 'POST':
        otp = request.POST.get('otp')
        voter = RegisteredVoters.objects.filter(phone=phone).first()

        if otp == voter.otp:
            voter.account_verified = True
            voter.save()
            messages.success(request, 'OTP verified, You can now log in')
            return redirect('login')
        else:
            print('Wrong OTP')
            messages.error(request, 'You entered wrong OTP')
            return render(request, 'register_otp.html', {'phone': phone})
    
    return render(request, 'register_otp.html', {'phone': phone})


def login_page(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            voter = RegisteredVoters.objects.get(username=username)
        except:
            messages.error(request, 'ID not registered')
            return redirect('login')

        if voter.vote_done:
            messages.error(request, 'You have already voted')
            return redirect('login')

        try:
            constituency = Constituency.objects.get(c_id=voter.c_id)
        except:
            messages.error(request, 'Error in contituency, please contact admin')
            return redirect('login')

        if not constituency.is_active:
            messages.error(request, 'Voting in your constituency is currently not active')
            return redirect('login')
        
        if not voter.account_verified:
            messages.error(request, 'Account not verified, Please verify your account')
            otp = str(random.randint(100000, 999999))
            voter.otp = otp
            voter.save()
            phone = voter.phone
            request.session['phone'] = phone
            send_otp(phone, otp)
            return redirect('register_otp')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            phone = user.phone
            otp = str(random.randint(100000, 999999))
            user.otp = otp
            user.save()
            request.session['phone'] = phone
            send_otp(phone, otp)
            messages.success(request, 'Verify to login')
            return redirect('login_otp')
        else:
            messages.error(request, 'Invalid credentials')
            return redirect('login')
    else:
        return render(request, 'login.html')


def login_otp(request):
    phone = request.session['phone']
    if request.method == 'POST':
        otp = request.POST.get('otp')
        voter = RegisteredVoters.objects.filter(phone=phone).first()

        if otp == voter.otp:
            login(request, voter)
            messages.success(request, 'OTP verified, Login successful')
            return redirect('home')
        else:
            print('Wrong OTP')
            messages.error(request, 'You entered wrong OTP')
            return render(request, 'login_otp.html', {'phone': phone})
    
    return render(request, 'login_otp.html', {'phone': phone})


def logout_page(request):
    logout(request)
    messages.success(request, 'You are now logged out')
    return redirect('home')


# ------------Voting Phase-----------------------

def home(request):
    if request.user.is_authenticated:
        global BLOCKCHAIN_NODE_ADDRESS
        constituency = Constituency.objects.get(c_id=request.user.c_id)
        BLOCKCHAIN_NODE_ADDRESS = constituency.node_address
        print("constituency address: ", constituency.node_address)
        print("CONSTITUENCY ADDRESS: ", BLOCKCHAIN_NODE_ADDRESS)
    return render(request, 'landing.html')


@login_required(login_url='login')
def voting(request):
    constituency = Constituency.objects.get(c_id=request.user.c_id)
    if request.user.vote_done:
        messages.error(request, 'You cannot vote more than once')
        return redirect('home')
    
    if not constituency.is_active:
        messages.error(request, 'Voting in your constituency is currently not active')
        return redirect('home')
        
    return render(request, 'voting.html', {'constituency': constituency})


@login_required(login_url='login')
def submit(request):
    if request.method == 'POST':
        data = request.POST

        if request.user.is_authenticated:
            voter = RegisteredVoters.objects.get(username=request.user.username)
            voter_hash_string = str(request.user.username) + str(request.user.email) + str(request.user.name) + str(request.user.phone) + str(request.user.age)
            voter_hashed_value = sha256(voter_hash_string.encode()).hexdigest()

            vote_transaction = {
                "candidate": request.POST.get('candidate'),
                "voterhash": voter_hashed_value
            }

            response = requests.post(f"{BLOCKCHAIN_NODE_ADDRESS}/new_transaction/", json=vote_transaction, headers={'Content-type': 'application/json'})

            response_data = response.json()
            print(response_data)

            if response.status_code == 201:
                voter.vote_done = True
                # voter.save()  # change this 
                return render(request, 'success.html', {'voter_details': data})
            else:
                return render(request, 'error.html', {'error_message': response_data['error']})
        else:
            return render(request, 'error.html', {'error_message': "NOT VALID"})


@login_required(login_url='login')
def success(request):
    return render(request, 'success.html')


@login_required(login_url='login')
def mine(request):
    requests.get(f"{BLOCKCHAIN_NODE_ADDRESS}/mine_block/")
    return redirect('mine_success')


@login_required(login_url='login')
def mine_success(request):
    return render(request, 'mine_success.html')


# ------------Result-----------------------

@login_required(login_url='login')
def all_votes(request):
    vote_data = []
    try:
        response = requests.get(f"{BLOCKCHAIN_NODE_ADDRESS}/chain")
    except:
        return render(request, '404.html')
    if response.status_code == 200:
        chain_data = json.loads(response.content)
        for block in chain_data["chain"]:
            for transaction in block["transactions"]:
                transaction["index"] = block["index"]
                vote_data.append(transaction)

        print("final", vote_data)
    
    response = requests.get(f"{BLOCKCHAIN_NODE_ADDRESS}/chain_validity")
    if response.status_code == 200:
        validity_message = json.loads(response.content)
        is_valid = True
        print(validity_message, is_valid)
    elif response.status_code == 400:
        validity_message = json.loads(response.content)
        is_valid = False
        print(validity_message, is_valid)
    
    return render(request, 'all_votes.html', { 'vote_details': vote_data, 'validity_message': validity_message, 'is_valid': is_valid})


def fetch_votes_and_count():
    vote_count = {}
    res = requests.get(f'{BLOCKCHAIN_NODE_ADDRESS}/chain')
    data = res.json()['chain']
    
    for i in data:
        for j in i['transactions']:
            if j['candidate'] in vote_count:
                vote_count[j['candidate']] += 1
            else:
                vote_count[j['candidate']] = 1
    return vote_count


@login_required(login_url='login')
def count_votes(request):
    try:
        data = fetch_votes_and_count()
    except:
        return render(request, '404.html')
    print("count_votes()", data)
    return render(request, 'count_votes.html', {'vote_count': data})


@login_required(login_url='login')
def chart_votes(request):
    try:
        data = fetch_votes_and_count()
    except:
        return render(request, '404.html')
    print("chart_votes()", data)
    keys_data = list(data.keys())
    print("chart", keys_data)
    values_data = list(data.values())
    print("chart", values_data)
    return render(request, 'count_votes_graph.html', {'count': values_data, 'names': keys_data})


# ------------Change Nodes-----------------------
@user_passes_test(lambda u: u.is_superuser)
def change_node(request):
    if request.method == 'POST':
        global BLOCKCHAIN_NODE_ADDRESS
        node_address = request.POST.get('nodeaddr')
        BLOCKCHAIN_NODE_ADDRESS = node_address
        return render(request, 'change_node_success.html', {'node_address': BLOCKCHAIN_NODE_ADDRESS})
    else:
        return render(request, 'change_node.html')


@user_passes_test(lambda u: u.is_superuser)
def register_node(request):
    if request.method == 'POST':
        global BLOCKCHAIN_NODE_ADDRESS
        node_address = request.POST.get('nodeaddr')
        headers = {
        'Content-Type': 'application/json',
        }

        data = '{'+f'"node_address": "{BLOCKCHAIN_NODE_ADDRESS}"'+'}'

        response = requests.post(f'{node_address}/register_with/', headers=headers, data=data)
        print(response.content)
        return render(request, 'register_node_success.html', {'registered_node': node_address})
    else:
        return render(request, 'register_node.html')


@user_passes_test(lambda u: u.is_superuser)
def connected_node(request):
    return render(request, 'connected_node.html', {'connected_node': BLOCKCHAIN_NODE_ADDRESS})

# ------------Blockchain calls-----------------------

# @csrf_exempt
# def new_transaction(request):
#     if request.method == 'POST':
#         transaction_data = json.loads(request.body)
#         print(transaction_data)
#         required_fields = ["candidate", "voterhash"]

#         for field in required_fields:
#             if not transaction_data.get(field):
#                 return JsonResponse({'error': 'Invalid transaction data'}, safe=False, status=404) 

#         if (transaction_data["voterhash"] in blockchain.voted):
#             return JsonResponse({'error': 'You cannot vote more than once'}, status=400)

#         transaction_data["timestamp"] = str(datetime.datetime.now())

#         blockchain.add_new_transaction(transaction_data)

#         return JsonResponse("Success", safe=False, status=201)


# def get_chain(request):
#     chain_data = []
#     for block in blockchain.chain:
#         chain_data.append(block.__dict__)

#     data = {
#         "length": len(chain_data),
#         "chain": chain_data
#     }
#     return JsonResponse(data, safe=False, status=200)


# def mine_block(request):
#     result = blockchain.mine()
#     if not result:
#         return JsonResponse("No transactions in queue to mine", safe=False, status=404)
#     else:
#         return JsonResponse(f"Block #{blockchain.last_block.index} is mined. Your vote is now added to the blockchain", safe=False, status=201)


# def pending_transaction(request):
#     return JsonResponse({'pending': blockchain.unconfirmed_transactions }, status=200)
