import matplotlib.pyplot as plt


def generate_report(data):
    categories = list(data.keys())
    values = list(data.values())

    plt.bar(categories, values)
    plt.xlabel('Категории')
    plt.ylabel('Сумма')
    plt.title('Распределение бюджета')
    plt.savefig('budget_report.png')
    return 'budget_report.png'
