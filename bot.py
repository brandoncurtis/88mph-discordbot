#!/usr/bin/env python

import requests
import datetime
import time
import random
import asyncio
import discord
import os
from discord.ext.commands import Bot
from discord.ext import commands, tasks
from web3 import Web3
from dotenv import load_dotenv

load_dotenv(override=True)
DISCORD_WEBHOOK_URL = os.getenv("WEBHOOK_URL")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
NODE_URL = os.getenv("NODE_URL")
START_BLOCK = os.getenv("START_BLOCK")
UNIROUTER_ADDR = os.getenv("UNIROUTER_ADDR")
UNIROUTER_ABI = os.getenv("UNIROUTER_ABI")
UNIPOOL_ADDR= os.getenv("UNIPOOL_ADDR")
UNIPOOL_ABI = os.getenv("UNIPOOL_ABI")
VAULT_ABI = os.getenv("VAULT_ABI")
PS_ABI = os.getenv("PS_ABI")
ONE_18DEC = 1000000000000000000
ONE_6DEC = 1000000
ZERO_ADDR = '0x0000000000000000000000000000000000000000'
UNIPOOL_ORACLE_ADDR = '0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc'
CIRCULATING_EXCLUDED = {
            'MPH': [
                '0xd48Df82a6371A9e0083FbfC0DF3AF641b8E21E44',
                '0x56f34826Cc63151f74FA8f701E4f73C5EAae52AD',
                '0xfecBad5D60725EB6fd10f8936e02fa203fd27E4b',
                '0x8c5ddBB0fd86B6480D81A1a5872a63812099C043',
            ]
            }

w3 = Web3(Web3.HTTPProvider(NODE_URL))
controller_contract = w3.eth.contract(address=UNIROUTER_ADDR, abi=UNIROUTER_ABI)
oracle_contract = w3.eth.contract(address=UNIPOOL_ORACLE_ADDR, abi=UNIPOOL_ABI)

client = discord.Client(command_prefix='!')
activity_start = discord.Streaming(name='network reboot',url='https://etherscan.io/address/0x284fa4627AF7Ad1580e68481D0f9Fc7e5Cf5Cf77')

update_index = 0

ASSETS = {
    'MPH': {
        'addr':'0x8888801aF4d980682e47f1A9036e589479e835C5',
        'pool':'0x4D96369002fc5b9687ee924d458A7E5bAa5df34E',
        'rewards':'',
        'poolnum':'token0'
        },
    'oldMPH': {
        'addr':'0x75A1169E51A3C6336Ef854f76cDE949F999720B1',
        'pool':'0xfd9aACca3c5F8EF3AAa787E5Cb8AF0c041D8875f',
        'rewards':'0x75A1169E51A3C6336Ef854f76cDE949F999720B1',
        'poolnum':'token0'
        }
}

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    await client.change_presence(activity=activity_start)
    update_price.start()

@tasks.loop(seconds=20)
async def update_price():
    global update_index
    asset = list(ASSETS.keys())[update_index % len(ASSETS)]
    token = ASSETS[asset]
    print(f'fetching pool reserves for {token["addr"]}...')
    pool_contract = w3.eth.contract(address=token['pool'], abi=UNIPOOL_ABI)
    poolvals = pool_contract.functions['getReserves']().call()
    oraclevals = oracle_contract.functions['getReserves']().call()
    print(f'calculating price...')
    oracle_price = controller_contract.functions['quote'](ONE_6DEC, oraclevals[0], oraclevals[1]).call()*10**-18
    print(f'oracle price: {oracle_price}')
    token_price = controller_contract.functions['quote'](ONE_18DEC, poolvals[0], poolvals[1]).call()*10**-18
    price = token_price / oracle_price
    print(f'updating the price...')
    msg = f'${price:0.2f} {asset}'
    new_price = discord.Streaming(name=msg,url='https://etherscan.io/address/0x284fa4627AF7Ad1580e68481D0f9Fc7e5Cf5Cf77')
    print(msg)
    await client.change_presence(activity=new_price)
    #update_index += 1

@client.event
async def on_message(msg):
    if client.user.id != msg.author.id: # and msg.channel.id == 775798003960643634:
        if '!foo' in msg.content:
            await msg.channel.send('bar')
        elif '!bot' in msg.content:
            embed = discord.Embed(
                    title='80s-themed AI assistant, at your service :sparkles:',
                    description=f':arrows_counterclockwise: `!reboot` info on the MPH88 reboot\n'
                                f':bar_chart: `!uniswap`: MPH markets and trading\n'
                                f':potable_water: `!supply`: MPH max and circulating supply\n'
                                f':thinking: `!incentives`: information on staking and liquidity rewards\n'
                                f':globe_with_meridians: `!contribute`: contribute to the community wiki (coming soon)\n'
                                f':chart_with_upwards_trend: improve me on GitHub (coming soon)'
                    )
            await msg.channel.send(embed=embed)
        elif '!reboot' in msg.content:
            embed = discord.Embed(
                    title='88MPH is being rebooted on November 19th',
                    description=f'**WHY:** two exploits; funds taken in the 1st exploit were reclaimed in the 2nd\n'
                                f'**HOW:** releasing a new MPH token based on a snapshot before the 2nd exploit\n'
                                f'**WHAT:** read announcements to [claim MPH](https://88mph.app/claim-mph) ([+ETH for LPs](https://88mph.app/claim-eth)) from the snapshot\n'
                                f'**WHEN:** farming restarts Nov 20th 20:00 GMT; capital deposits will reopen in a few days\n'
                                f'`NOTE!` when LPs claim ETH, it is in WETH form; [unwrap to ETH here](https://matcha.xyz/markets/ETH/WETH)\n'
                                f'`NOTE!` [old MPH](https://etherscan.io/token/{ASSETS["oldMPH"]["addr"]}) no longer has value.\n'
                                f'address of new MPH: [{ASSETS["MPH"]["addr"]}](https://etherscan.io/token/{ASSETS["MPH"]["addr"]})'
                    )
            await msg.channel.send(embed=embed)
        elif '!ap' in msg.content:
            val = float(msg.content.split(' ')[-1])
            # APY = (1 + APR / n) ** n - 1
            APYfromAPR_daily = 100 * ((1 + val / (100 * 365)) ** 365 - 1)
            APYfromAPR_weekly = 100 * ((1 + val / (100 * 52)) ** 52 - 1)
            # APR = n * (1 + APY) ** (1 / n) -n
            APRfromAPY_daily = 100 * (365 * ((1 + val / 100) ** (1 / 365)) - 365)
            APRfromAPY_weekly = 100 * (52 * ((1 + val / 100) ** (1 / 52)) - 52)
            embed = discord.Embed(
                    title=':man_teacher: **Convert between APR and APY?**',
                    )
#            embed.add_field(name = 'Compounded Daily', value = 'If you redeem and reinvest rewards daily...', inline=False)
#            embed.add_field(
#                    name = f'APR to APY',
#                    value = f'{val:,.2f}% APR is equal to {APYfromAPR_daily:,.2f}% APY. $1000 will make about ${1000*val/100/365:,.2f} per day.',
#                    inline = True
#                    )
#            embed.add_field(
#                    name = f'APY to APR',
#                    value = f'{val:,.2f}% APY is equal to {APRfromAPY_daily:,.2f}% APR. $1000 will make about ${1000*APRfromAPY_daily/100/365:,.2f} per day.',
#                    inline = True
#                    )
            embed.add_field(name = 'Compounded Weekly', value = 'If you redeem and reinvest rewards weekly...', inline=False)
            embed.add_field(
                    name = f'APR to APY',
                    value = f'{val:,.2f}% APR is equal to {APYfromAPR_weekly:,.2f}% APY. $1000 will make about ${1000*val/100/365:,.2f} per day.',
                    inline = True
                    )
            embed.add_field(
                    name = f'APY to APR',
                    value = f'{val:,.2f}% APY is equal to {APRfromAPY_weekly:,.2f}% APR. $1000 will make about ${1000*APRfromAPY_weekly/100/365:,.2f} per day.',
                    inline = True
                    )
            await msg.channel.send(embed=embed)
        elif '!uniswap' in msg.content:
            asset = 'MPH'
            uni_addr, uni_deposit_token, uni_deposit_pairing, uni_token_frac = get_uniswapstate(asset)
            embed = discord.Embed(
                    title=f':mag: MPH:ETH Uniswap Pool',
                    description=f':bank: Uniswap contract: [{uni_addr}](https://etherscan.io/address/{uni_addr})\n'
                                f':moneybag: Liquidity: `{uni_deposit_token:,.2f}` {asset} (`{100*uni_token_frac:.2f}%` of supply), `{uni_deposit_pairing:,.2f}` ETH\n'
                                f':arrows_counterclockwise: [Trade {asset}](https://app.uniswap.org/#/swap?outputCurrency={ASSETS[asset]["addr"]}), '
                                f'[Add Liquidity](https://app.uniswap.org/#/add/eth/{ASSETS[asset]["addr"]}), '
                                f'[Remove Liquidity](https://app.uniswap.org/#/remove/ETH/{ASSETS[asset]["addr"]})\n'
                                f':bar_chart: [{asset}:ETH Uniswap chart](https://www.dextools.io/app/uniswap/pair-explorer/{uni_addr})'
                    )
            await msg.channel.send(embed=embed)
        elif '!incentives' in msg.content or '!farm' in msg.content:
            embed = discord.Embed(
                    title='How do I farm 88MPH?',
                    description=f'**Short term:** provide liquidity in the ETH:MPH Uniswap pool (14 days, starts Nov 20th 20:00 GMT)\n'
                                f'**Long term:** stake MPH to receive a share of investment profits\n'
                                f'**Alternative:** deposit funds to receive MPH; 90% must be paid back to withdraw!\n'
                                f'(early withdrawals require up to 100% payback of received MPH)'
                    )
            await msg.channel.send(embed=embed)
        elif '!supply' in msg.content:
            asset = 'MPH'
            supply = get_supply('MPH')
            circulating = get_supply_circulating('MPH')
            circulating_frac = circulating / supply
            uni_supply = get_supply('MPH', ASSETS[asset]['pool'])
            uni_supply_frac = uni_supply / supply
            embed = discord.Embed(
                    title=f':bar_chart: Current and maximum supply of MPH?',
                    description=f'**Max Supply:** maximum supply is unlimited\n'
                    f'**Total Supply:** `{supply:,.2f}` {asset}, `{uni_supply:,.2f}` {asset} (`{100*uni_supply_frac:.2f}%`) in Uniswap\n'
                    f'**Circulating:** `{circulating:,.2f}` {asset} (`{100*circulating_frac:.2f}%`)\n'
                    f'**Distribution:** by liquidity mining and to capital depositors\n'
                    f'90% of deposit incentives are paid back to the Treasury at redemption;\n'
                    f'the community can decide to issue more incentives, pay for development, burn...'
                    )
            await msg.channel.send(embed=embed)
        else:
            return

def get_supply_circulating(asset):
    token_contract = w3.eth.contract(address=ASSETS[asset]['addr'], abi=UNIPOOL_ABI)
    token_decimals = token_contract.functions['decimals']().call()
    token_totalsupply = token_contract.functions['totalSupply']().call()*10**(-1*token_decimals)
    token_circulating = token_totalsupply
    for excluded_addr in CIRCULATING_EXCLUDED[asset]:
        token_circulating = token_circulating - token_contract.functions['balanceOf'](excluded_addr).call()*10**(-1*token_decimals)
    return token_circulating

def get_supply(asset, address=''):
    token_contract = w3.eth.contract(address=ASSETS[asset]['addr'], abi=UNIPOOL_ABI)
    token_decimals = token_contract.functions['decimals']().call()
    if address != '':
        token_balance = token_contract.functions['balanceOf'](address).call()*10**(-1*token_decimals)
        return token_balance
    else: 
        token_totalsupply = token_contract.functions['totalSupply']().call()*10**(-1*token_decimals)
        return token_totalsupply

def get_uniswapstate(asset):
    uni_addr = ASSETS[asset]['pool']
    pool_contract = w3.eth.contract(address=uni_addr, abi=UNIPOOL_ABI)
    poolvals = pool_contract.functions['getReserves']().call()
    uni_deposit_token = poolvals[0]*10**-18
    uni_deposit_pairing = poolvals[1]*10**-18
    token_totalsupply = get_supply(asset)
    uni_token_frac = uni_deposit_token / token_totalsupply
    return (uni_addr, uni_deposit_token, uni_deposit_pairing, uni_token_frac)


def get_profitsharestate():
    ps_address = vault_addr['profitshare']['addr']
    ps_contract = w3.eth.contract(address=ps_address, abi=PS_ABI)
    lp_addr = ps_contract.functions['lpToken']().call()
    lp_contract = w3.eth.contract(address=lp_addr, abi=VAULT_ABI)
    ps_decimals = lp_contract.functions['decimals']().call()
    lp_totalsupply = lp_contract.functions['totalSupply']().call()*10**(-1*ps_decimals)
    ps_rewardrate = ps_contract.functions['rewardRate']().call()
    ps_totalsupply = ps_contract.functions['totalSupply']().call()*10**(-1*ps_decimals)
    ps_rewardfinish = ps_contract.functions['periodFinish']().call()
    ps_rewardperday = ps_rewardrate * 3600 * 24 * 10**(-1*ps_decimals)
    ps_rewardfinishdt = datetime.datetime.fromtimestamp(ps_rewardfinish)
    ps_stake_frac = ps_totalsupply / lp_totalsupply
    return (ps_totalsupply, ps_rewardperday, ps_rewardfinishdt, ps_stake_frac)

def get_vaultstate(vault):
    vault_address = vault_addr[vault]['addr']
    vault_contract = w3.eth.contract(address=vault_address, abi=VAULT_ABI)
    vault_strat = vault_contract.functions['strategy']().call()
    vault_strat_future = vault_contract.functions['futureStrategy']().call()
    vault_strat_future_time = int(vault_contract.functions['strategyUpdateTime']().call())
    vault_decimals = int(vault_contract.functions['decimals']().call())
    vault_shareprice = vault_contract.functions['getPricePerFullShare']().call()*10**(-1*vault_decimals)
    vault_total = vault_contract.functions['underlyingBalanceWithInvestment']().call()*10**(-1*vault_decimals)
    vault_buffer = vault_contract.functions['underlyingBalanceInVault']().call()*10**(-1*vault_decimals)
    vault_target_numerator = vault_contract.functions['vaultFractionToInvestNumerator']().call()
    vault_target_denominator = vault_contract.functions['vaultFractionToInvestDenominator']().call()
    vault_target = vault_target_numerator / vault_target_denominator
    return (vault_address, vault_shareprice, vault_total, vault_buffer, vault_target, vault_strat, vault_strat_future, vault_strat_future_time)

def main():
    print(f'starting discord bot...')
    client.run(DISCORD_BOT_TOKEN)
    print(f'discord bot started')

if __name__ == '__main__':
    main()
