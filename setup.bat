@echo off
REM 创建项目目录结构
mkdir financial_report_parser\config
mkdir financial_report_parser\data
mkdir financial_report_parser\data\annual
mkdir financial_report_parser\src
mkdir financial_report_parser\doc
mkdir financial_report_parser\logs

REM 创建必要的Python包初始化文件
type nul > financial_report_parser\config\__init__.py
type nul > financial_report_parser\src\__init__.py

REM 创建其他必要文件
type nul > financial_report_parser\.env
type nul > financial_report_parser\requirements.txt
type nul > financial_report_parser\main.py
type nul > financial_report_parser\src\utils.py

echo Setup completed! 