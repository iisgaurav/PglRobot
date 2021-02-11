@echo off
TITLE PglRobot
:: Enables virtual env mode and then starts PglRobot
env\scripts\activate.bat && py -m PglRobot
