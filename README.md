# Politisk Parti Chatbot

Dette er en webapplikasjon som lar deg utforske og sammenligne norske politiske partiprogrammer på en interaktiv måte. Bruk den innebygde quizen for å finne ut hvilket parti som best matcher dine synspunkter, eller still direkte spørsmål til partiprogrammene for å få dybdeinnsikt i spesifikke politiske saker.

Applikasjonen bruker Google Gemini, en avansert språkmodell, til å analysere og presentere informasjon direkte fra partienes offisielle programmer.

## Funksjoner

- **Politisk Quiz**: Svar på 5 åpne spørsmål for å få en analyse av hvilke partiprogrammer som samsvarer best med dine meninger.
- **Direkte Spørsmål (Q&A)**: Still spørsmål om ett eller flere partier for å få detaljerte svar basert på deres programmer.
- **Sammenligning**: Spør generelt om et tema (f.eks. "Hva mener partiene om miljø?") for å få en sammenligning av standpunktene til alle partiene.
- **Brukervennlig Grensesnitt**: Enkel og intuitiv navigasjon med to hovedmoduser: Quiz og Chat.
- **"Om Appen"-side**: En informativ side som forklarer hvordan appen fungerer og inkluderer en ansvarsfraskrivelse om bruk av språkmodeller.

<img width="1240" height="821" alt="Screenshot 2025-08-03 at 10 07 18" src="https://github.com/user-attachments/assets/21fa7c9c-3f41-410e-920b-98104ca54838" />

<img width="1235" height="820" alt="Screenshot 2025-08-03 at 10 08 52" src="https://github.com/user-attachments/assets/dc37a907-1d2d-44e7-a6ad-49bf605e56e5" />

<img width="1486" height="821" alt="Screenshot 2025-08-03 at 10 19 00" src="https://github.com/user-attachments/assets/a35786b3-bc8b-4f01-b9d7-c1afaad2e26c" />


## Teknologioversikt

- **Backend**: Python med Flask
- **Språkmodell (LLM)**: Google Gemini 1.5 Flash
- **Frontend**: Standard HTML, CSS og JavaScript
- **Styling**: Tailwind CSS
- **Tekst-analyse**: Fuzzywuzzy for gjenkjenning av partinavn

## Installasjon og Kjøring

Følg disse stegene for å kjøre applikasjonen lokalt på din maskin.

### 1. Klon repositoriet
Åpne en terminal og klon dette repositoriet til din lokale maskin:
```bash
git clone https://github.com/ditt-brukernavn/partiprogram_llm.git
cd partiprogram_llm
```

### 2. Opprett et virtuelt miljø
Det er anbefalt å bruke et virtuelt miljø for å håndtere prosjektets avhengigheter.
```bash
# For macOS/Linux
python3 -m venv venv
source venv/bin/activate

# For Windows
python -m venv venv
.\venv\Scripts\activate
```

### 3. Installer avhengigheter
Installer alle nødvendige Python-pakker fra `requirements.txt`:
```bash
pip install -r requirements.txt
```

### 4. Sett opp API-nøkkel
For at appen skal kunne kommunisere med Google Gemini, trenger du en API-nøkkel.

1.  Opprett en fil ved navn `.env` i rotmappen til prosjektet.
2.  Gå til [Google AI Studio](https://aistudio.google.com/app/apikey) for å opprette din egen API-nøkkel.
3.  Legg til nøkkelen i `.env`-filen på følgende format:
    ```
    GEMINI_API_KEY="DIN_API_NØKKEL_HER"
    ```

### 5. Kjør applikasjonen
Når alt er installert og konfigurert, kan du starte Flask-serveren:
```bash
python app.py
```
Applikasjonen vil nå være tilgjengelig i din nettleser på `http://127.0.0.1:8080`.

## Bruk

Når du åpner applikasjonen, blir du møtt med to valg:

1.  **Ta den politiske quizen**: Start en 5-spørsmåls quiz for å få en analyse av din politiske tilhørighet.
2.  **Spør om partiprogrammer**: Gå direkte til en chat hvor du kan stille spørsmål som:
    - "Hva mener Høyre om formuesskatt?"
    - "Sammenlign politikken til Arbeiderpartiet og Senterpartiet på landbruk."
    - "Hva er partienes syn på oljeboring?"

## Ansvarsfraskrivelse

Denne applikasjonen bruker store språkmodeller (LLMs) for å generere svar. Selv om målet er å gi nøyaktig og nøytral informasjon basert på partiprogrammene, kan språkmodeller noen ganger gjøre feil, feiltolke kontekst eller "hallusinere" (finne på) informasjon. Svarene bør derfor brukes som en veiledning og ikke som en absolutt fasit. For å være helt sikker på et partis standpunkt, anbefales det alltid å konsultere de offisielle partiprogrammene.
