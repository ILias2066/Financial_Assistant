from aiogram.filters import Command, StateFilter
from aiogram import Router
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from keyboards.kb import kb
from keyboards.command import set_commands
from database.db import SessionLocal, UserBudget
from sqlalchemy.future import select
import io

router = Router()


class Form(StatesGroup):
    savings = State()
    credit = State()
    expenses = State()
    income = State()


async def save_user_budget(state: FSMContext, user_id: str):
    user_data = await state.get_data()

    async with SessionLocal() as session:
        stmt = select(UserBudget).filter(UserBudget.telegram_id == user_id)
        result = await session.execute(stmt)
        user_budget = result.scalars().first()

        if user_budget is None:
            user_budget = UserBudget(
                telegram_id=user_id,
                monthly_income=user_data.get("monthly_income"),
                savings_percent=user_data.get("savings_percent"),
                credit_payment=user_data.get("credit_payment"),
                expenses=user_data.get("expenses", {}),
            )
            session.add(user_budget)
        else:
            user_budget.monthly_income = user_data.get("monthly_income")
            user_budget.savings_percent = user_data.get("savings_percent")
            user_budget.credit_payment = user_data.get("credit_payment")
            user_budget.expenses = user_data.get("expenses", {})

        await session.commit()

def parse_expenses(expenses_data):
    expenses = {}
    for item in expenses_data.split(','):
        parts = item.split()
        if len(parts) != 2:
            continue
        category, amount = parts
        try:
            expenses[category] = int(amount)
        except ValueError:
            continue
    return expenses

def generate_pdf(expenses_data):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.drawString(100, 750, "Отчет о расходах:")
    y = 730
    for category, amount in expenses_data.items():
        c.drawString(100, y, f"{category}: {amount} руб.")
        y -= 20
    c.showPage()
    c.save()

    buffer.seek(0)
    return buffer

@router.message(Command('start'))
async def get_start(message: Message, state: FSMContext):
    await message.answer(f'Привет, {message.from_user.first_name}!', reply_markup=kb)
    await message.answer(
        "Добро пожаловать! Давайте настроим ваш бюджет. "
        "Сколько процентов от дохода вы хотите откладывать? Например, введите 20."
    )
    await state.set_state(Form.savings)
    await set_commands(message.bot)

@router.message(StateFilter(Form.savings))
async def get_savings(message: Message, state: FSMContext):
    try:
        savings_percent = int(message.text)
        if savings_percent < 0:
            raise ValueError
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число. Например, 20.")
        return

    await state.update_data(savings_percent=savings_percent)
    await message.answer("Какой у вас месячный доход? Например, введите 50000.")
    await state.set_state(Form.income)

@router.message(StateFilter(Form.income))
async def get_income(message: Message, state: FSMContext):
    try:
        monthly_income = int(message.text)
        if monthly_income <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Пожалуйста, введите корректную сумму. Например, 50000.")
        return

    await state.update_data(monthly_income=monthly_income)
    skip_keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Пропустить")]], resize_keyboard=True
    )
    await message.answer("Сколько вы платите за кредит? Нажмите 'Пропустить', если нет.", reply_markup=skip_keyboard)
    await state.set_state(Form.credit)

@router.message(StateFilter(Form.credit))
async def process_credit(message: Message, state: FSMContext):
    credit_payment = message.text
    if credit_payment.lower() == "пропустить":
        credit_payment = 0
    else:
        try:
            credit_payment = int(credit_payment)
            if credit_payment < 0:
                raise ValueError
        except ValueError:
            await message.answer("Введите корректную сумму или 'Пропустить'.")
            return

    await state.update_data(credit_payment=credit_payment)
    await message.answer("Введите ваши расходы в формате: питание 5000, транспорт 2000.")
    await state.set_state(Form.expenses)

# Сохранение расходов и завершение настройки
@router.message(StateFilter(Form.expenses))
async def process_expenses(message: Message, state: FSMContext):
    expenses_data = message.text
    expenses = parse_expenses(expenses_data)

    if not expenses:
        await message.answer("Введите хотя бы одну категорию в формате: 'категория сумма'.")
        return

    await state.update_data(expenses=expenses)

    user_data = await state.get_data()
    monthly_income = user_data['monthly_income']
    savings_percent = user_data['savings_percent']
    credit_payment = user_data['credit_payment']

    savings_amount = (monthly_income * savings_percent) / 100
    remaining_income = monthly_income - savings_amount - credit_payment - sum(expenses.values())

    await save_user_budget(state, str(message.from_user.id))

    response = f"""
<b>Ваш бюджет настроен:</b>
- <b>Доход:</b> {monthly_income} руб.
- <b>Сбережения:</b> {savings_amount} руб. ({savings_percent}%)
- <b>Кредиты:</b> {credit_payment} руб.
- <b>Оставшийся доход:</b> {remaining_income} руб.

<b>Дополнительные расходы:</b>
{"".join([f"- {category}: {amount} руб.\n" for category, amount in expenses.items()])}
"""
    await message.answer(response, parse_mode="HTML")
    await message.answer("Ваши данные сохранены!")
    await state.clear()

@router.message(Command('report'))
async def send_report(message: Message, state: FSMContext):
    # Получаем данные о расходах из состояния
    user_data = await state.get_data()
    user_expenses = user_data.get('expenses', {})

    # Если данных о расходах нет, сообщаем пользователю
    if not user_expenses:
        await message.answer("У вас ещё нет данных о расходах.")
        return

    # Генерируем отчет
    report_file = generate_pdf(user_expenses)

    # Отправляем PDF-файл пользователю
    await message.answer_document(io.BytesIO(report_file.read()), caption="Ваш отчет.")