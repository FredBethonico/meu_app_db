from flask import Flask, request, render_template_string, redirect, url_for
import json
import os
from datetime import datetime

app = Flask(__name__)

# ==========================================
# ⚙️ CONFIGURAÇÃO DO FORMULÁRIO
# ==========================================
DB_FILE = 'meu_banco.json'

# Defina seus campos aqui. 
FORM_CONFIG = [
    {
        "name": "categoria",
        "label": "📂 Categoria",
        "type": "select",
        "options": ["Comida", "Leitura", "Vídeo", "Áudio", "Jogo"]
    },
    {
        "name": "titulo",
        "label": "🏷️ Título / Item",
        "type": "text",
        "placeholder": "Ex: Milkshake, O Alienista..."
    },
    {
        "name": "autor",
        "label": "✍️ Autor / Diretor",
        "type": "text",
        "placeholder": "Quem escreveu/dirigiu?",
        "show_if": {
            "field": "categoria",
            "values": ["Leitura", "Vídeo", "Áudio"]
        }
    },
    {
        "name": "local",
        "label": "📍 Local de Compra/Consumo",
        "type": "text",
        "placeholder": "Ex: Mart Minas, Padaria Pão Nosso...",
        "show_if": {
            "field": "categoria",
            "values": ["Comida"]
        }
    },    
    {
        "name": "preco",
        "label": "💲 Preço (R$)",
        "type": "number",
        "step": "0.01",
        "min": "0.0",
        "placeholder": "Ex: 29,99", # Atualizei o placeholder para sugerir vírgula
        "show_if": {
            "field": "categoria",
            "values": ["Comida"]
        }
    },
    {
        "name": "ano_lancamento",
        "label": "📆 Ano de Lançamento",
        "type": "number",
        "show_if": {
            "field": "categoria",
            "values": ["Vídeo", "Áudio", "Jogo"]
        }
    },
    {
        "name": "nota",
        "label": "🔢 Nota (0,0 a 5,0)",
        "type": "number",
        "step": "0.5", 
        "min": "0.0",
        "max": "5.0",
        "placeholder": "Ex: 4,5" # Sugestão com vírgula
    },
    {
        "name": "data_ref",
        "label": "📅 Data de Referência",
        "type": "date",
    },
    {
        "name": "obs",
        "label": "📝 Observações",
        "type": "textarea",
        "placeholder": "Detalhes adicionais..."
    }
]

# ==========================================
# 🎨 TEMPLATE HTML DINÂMICO + JS
# ==========================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Coletor de Dados</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; padding: 15px; background: #f0f2f6; color: #333; }
        .card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px; }
        h2 { margin-top: 0; color: #0e1117; font-size: 1.5rem; }
        
        .form-group { margin-bottom: 15px; transition: all 0.3s ease; }
        .hidden { display: none; } 

        label { display: block; font-weight: 500; font-size: 0.9rem; margin-bottom: 5px; }
        
        input, select, textarea { 
            width: 100%; padding: 12px; border: 1px solid #ddd; 
            border-radius: 8px; box-sizing: border-box; font-size: 16px; 
            background-color: #fff;
        }
        input:focus, select:focus, textarea:focus { border-color: #ff4b4b; outline: none; }
        
        button { 
            width: 100%; background-color: #ff4b4b; color: white; 
            padding: 15px; margin-top: 10px; border: none; border-radius: 8px; 
            font-size: 16px; font-weight: bold; cursor: pointer; 
        }
        button:hover { background-color: #ff3333; }
        
        .history-item { 
            background: #f8f9fa; border-left: 4px solid #ff4b4b; 
            padding: 10px; margin-bottom: 10px; border-radius: 4px; font-size: 0.85rem;
        }
    </style>
</head>
<body>
    <div class="card">
        <h2>Inserir Dados</h2>
        <form method="POST" id="mainForm">
            
            {% for field in config %}
            <div class="form-group {% if field.show_if %}hidden{% endif %}" 
                 id="group-{{ field.name }}"
                 data-name="{{ field.name }}"
                 {% if field.show_if %}
                    data-condition-field="{{ field.show_if.field }}"
                    data-condition-values='{{ field.show_if["values"] | tojson }}'
                 {% endif %}>

                <label>{{ field.label }}</label>
                
                {% if field.type == 'select' %}
                    <select name="{{ field.name }}" id="input-{{ field.name }}">
                        {% for opt in field.options %}
                            <option value="{{ opt }}">{{ opt }}</option>
                        {% endfor %}
                    </select>
                
                {% elif field.type == 'textarea' %}
                    <textarea name="{{ field.name }}" rows="3" placeholder="{{ field.placeholder or '' }}"></textarea>
                
                {% else %}
                    <input type="{{ field.type }}" name="{{ field.name }}" 
                           step="{{ field.step or 'any' }}" 
                           min="{{ field.min or '' }}"
                           max="{{ field.max or '' }}"
                           placeholder="{{ field.placeholder or '' }}">
                {% endif %}
            </div>
            {% endfor %}
            
            <button type="submit">Salvar Registro</button>
        </form>
    </div>

    {% if ultimos_dados %}
    <div style="margin-top: 30px;">
        <h3 style="font-size: 1.1rem;">Últimos Registros</h3>
        {% for item in ultimos_dados %}
            <div class="history-item">
                <div class="history-meta">{{ item.timestamp }}</div>
                {% for key, val in item.items() %}
                    {% if key != 'timestamp' and val %}
                        <strong>{{ key }}:</strong> {{ val }} <br>
                    {% endif %}
                {% endfor %}
            </div>
        {% endfor %}
    </div>
    {% endif %}

    <script>
        document.addEventListener("DOMContentLoaded", function() {
            const form = document.getElementById('mainForm');
            const conditionalDivs = document.querySelectorAll('[data-condition-field]');

            function checkConditions() {
                conditionalDivs.forEach(div => {
                    const parentName = div.dataset.conditionField;
                    const allowedValues = JSON.parse(div.dataset.conditionValues);
                    
                    const parentInput = form.querySelector(`[name="${parentName}"]`);
                    
                    if (parentInput) {
                        if (allowedValues.includes(parentInput.value)) {
                            div.classList.remove('hidden');
                        } else {
                            div.classList.add('hidden');
                            const input = div.querySelector('input, select, textarea');
                            if(input) input.value = ""; 
                        }
                    }
                });
            }

            const allInputs = form.querySelectorAll('input, select, textarea');
            allInputs.forEach(input => {
                input.addEventListener('change', checkConditions);
                input.addEventListener('input', checkConditions);
            });

            checkConditions();
        });
    </script>
</body>
</html>
"""

# ==========================================
# 🧠 LÓGICA PYTHON
# ==========================================

def load_data():
    if not os.path.exists(DB_FILE):
        return []
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def save_data(new_entry):
    data = load_data()
    data.append(new_entry)
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False) 

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        for field in FORM_CONFIG:
            field_name = field['name']
            user_input = request.form.get(field_name)
            
            # Validação condicional
            if 'show_if' in field:
                trigger_field = field['show_if']['field']
                allowed_values = field['show_if']['values']
                actual_trigger_val = request.form.get(trigger_field)
                
                if actual_trigger_val not in allowed_values:
                    user_input = None 

            # Conversão Numérica (Agora aceita vírgula!)
            if field['type'] == 'number' and user_input:
                try:
                    # AQUI ESTÁ A MÁGICA: Substitui vírgula por ponto
                    clean_val = user_input.replace(',', '.')
                    entry[field_name] = float(clean_val)
                except:
                    # Se falhar (ex: texto aleatório), salva como string mesmo
                    entry[field_name] = user_input
            else:
                entry[field_name] = user_input

        save_data(entry)
        return redirect(url_for('index'))
    
    dados = load_data()
    return render_template_string(HTML_TEMPLATE, ultimos_dados=dados[-5:][::-1], config=FORM_CONFIG)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
