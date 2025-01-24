# Example

## Table of Contents

- [Create a Virtual Environment](#create-a-virtual-environment)
- [Install Dependencies](#install-dependencies)
- [Update Configuration](#update-configuration)
- [Run](#run)

## Create a Virtual Environment <a id="create-a-virtual-environment"></a>

**uv (Recommended)**

```bash
uv venv
```

Once you have created a virtual environment, you may activate it.

On Unix or MacOS, run:

```bash
source .venv/bin/activate
```

On Windows, run:

```powershell
.venv\Scripts\activate
```

To deactivate the virtual environment, run:

```bash
deactivate
```

> [!TIP]
> More information about virtual environments can be found [here](https://docs.python.org/3/tutorial/venv.html).

## Install Dependencies

```bash
uv sync
playwright install --with-deps chromium
```

---

> [!NOTE]
> Alternatively, here are some of the most popular Python package and project managers, if you have opted to not use `uv`.
>
> **Poetry**
>
> ```bash
> # Create a virtual environment
> poetry shell
>
> # Install dependencies
> poetry install
> ```
>
> **Anaconda**
>
> ```bash
> # Create a virtual environment
> conda create -n venv python=3.12 -y
> conda activate venv
>
> # Install dependencies
> pip install -r requirements.txt
> ```

## Update Configuration <a id="update-configuration"></a>

If you used AZD to deploy the resources, simply run the code below:

```bash
azd env get-values > .env
```

Alternatively, copy [`.env.sample`](.env.sample) into `.env`.

> [!IMPORTANT]
> Magentic-One code uses code execution, you need to have Docker installed to run the examples if you use local execution.

## Run

```python
python m13.py
```

After the script finishes running, you will see a Python script generated in the current directory. In the case of this example, a file named [`elon_musk_tax_estimation.py`](elon_musk_tax_estimation.py) is created.

> [!TIP]
> Refer to the generated Python script to see what the Coder agent has generated based on the user query.
