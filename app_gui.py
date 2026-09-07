# -*- coding: utf-8 -*-
"""
app_gui.py — Ventana gráfica para generar el álbum de SPD sin usar la
línea de comandos.

Ejecutar con:
    python app_gui.py
"""
import os
import queue
import shutil
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from generar_album import generar
import acontecimientos as acontecimientos_mod

COLOR_FONDO = '#f4f2ee'
COLOR_ACENTO = '#1a1a1a'


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Álbum de Sobres de Primer Día — Pedro Antonio Vega Polo')
        self.geometry('720x960')
        self.configure(bg=COLOR_FONDO)
        self.resizable(True, True)

        self.csv_path = tk.StringVar()
        self.imagenes_dir = tk.StringVar()
        self.salida_dir = tk.StringVar(value=os.path.join(os.getcwd(), 'salida'))
        self.anio = tk.StringVar(value='1965')
        self.lineas_resumen = tk.IntVar(value=1)
        self.escala_imagen = tk.IntVar(value=100)

        self._log_queue = queue.Queue()
        self._resultado = None

        self._construir_ui()
        self._actualizar_acontecimiento()
        self.after(100, self._procesar_cola)

    # ------------------------------------------------------------------
    def _fila(self, parent, etiqueta):
        frame = ttk.Frame(parent)
        frame.pack(fill='x', pady=4)
        ttk.Label(frame, text=etiqueta, width=20).pack(side='left')
        return frame

    def _construir_ui(self):
        estilo = ttk.Style(self)
        try:
            estilo.theme_use('clam')
        except tk.TclError:
            pass
        estilo.configure('TButton', padding=6)
        estilo.configure('Titulo.TLabel', font=('Helvetica', 15, 'bold'))

        cont = ttk.Frame(self, padding=16)
        cont.pack(fill='both', expand=True)

        ttk.Label(cont, text='Álbum de Sobres de Primer Día', style='Titulo.TLabel').pack(anchor='w')
        ttk.Label(cont, text='Rellena los datos y pulsa "Generar álbum".').pack(anchor='w', pady=(0, 12))

        # CSV
        f = self._fila(cont, 'CSV del catálogo:')
        ttk.Entry(f, textvariable=self.csv_path).pack(side='left', fill='x', expand=True, padx=(0, 6))
        ttk.Button(f, text='Examinar…', command=self._elegir_csv).pack(side='left')

        # Carpeta de imágenes
        f = self._fila(cont, 'Carpeta de imágenes:')
        ttk.Entry(f, textvariable=self.imagenes_dir).pack(side='left', fill='x', expand=True, padx=(0, 6))
        ttk.Button(f, text='Examinar…', command=self._elegir_imagenes).pack(side='left')

        # Año
        f = self._fila(cont, 'Año:')
        spin_anio = ttk.Spinbox(f, from_=1850, to=2030, textvariable=self.anio, width=10,
                                 command=self._actualizar_acontecimiento)
        spin_anio.pack(side='left')
        spin_anio.bind('<Return>', lambda e: self._actualizar_acontecimiento())
        spin_anio.bind('<FocusOut>', lambda e: self._actualizar_acontecimiento())

        # Acontecimiento del año (portada) — editable
        ttk.Label(cont, text='Acontecimientos del año (para la portada):').pack(
            anchor='w', pady=(8, 2))

        self.campos_acontecimiento = {}
        etiquetas = [
            ('mundial_1', 'Mundial 1:'), ('mundial_2', 'Mundial 2:'),
            ('espana_1', 'España 1:'), ('espana_2', 'España 2:'),
        ]
        acont_frame = ttk.Frame(cont)
        acont_frame.pack(fill='x')
        for clave, etiqueta in etiquetas:
            f = ttk.Frame(acont_frame)
            f.pack(fill='x', pady=1)
            ttk.Label(f, text=etiqueta, width=30).pack(side='left')
            var = tk.StringVar()
            ttk.Entry(f, textvariable=var).pack(side='left', fill='x', expand=True)
            self.campos_acontecimiento[clave] = var

        self.campos_tipo = {}
        for n, clave_txt, clave_tipo in [(1, 'personal_1', 'personal_1_tipo'),
                                          (2, 'personal_2', 'personal_2_tipo')]:
            f = ttk.Frame(acont_frame)
            f.pack(fill='x', pady=1)
            etiqueta = f'Personal {n} ({"sello pareja" if n == 1 else "sello individual"}):'
            ttk.Label(f, text=etiqueta, width=30).pack(side='left')
            var = tk.StringVar()
            ttk.Entry(f, textvariable=var).pack(side='left', fill='x', expand=True)
            self.campos_acontecimiento[clave_txt] = var
            var_tipo = tk.StringVar(value='ninguno')
            ttk.Combobox(f, textvariable=var_tipo, width=13, state='readonly',
                         values=['ninguno', 'boda', 'nacimiento', 'fallecimiento', 'viaje', 'compra']).pack(
                side='left', padx=(6, 0))
            self.campos_tipo[clave_tipo] = var_tipo

        # Sobre de Primer Día destacado del año (opcional)
        self.campos_imagen = {}
        f = ttk.Frame(acont_frame)
        f.pack(fill='x', pady=1)
        ttk.Label(f, text='FDC destacado del año:', width=30).pack(side='left')
        var_fdc = tk.StringVar()
        ttk.Entry(f, textvariable=var_fdc).pack(side='left', fill='x', expand=True)
        self.campos_acontecimiento['fdc_destacado'] = var_fdc

        f = ttk.Frame(acont_frame)
        f.pack(fill='x', pady=1)
        ttk.Label(f, text='Imagen del FDC destacado (opcional):', width=30).pack(side='left')
        var_img_fdc = tk.StringVar()
        ttk.Entry(f, textvariable=var_img_fdc, state='readonly').pack(side='left', fill='x', expand=True)
        ttk.Button(f, text='Examinar…',
                   command=lambda: self._elegir_imagen_portada('fdc')).pack(side='left', padx=(6, 0))
        ttk.Button(f, text='Quitar', width=7,
                   command=lambda: self.campos_imagen['imagen_fdc'].set('')).pack(side='left', padx=(4, 0))
        self.campos_imagen['imagen_fdc'] = var_img_fdc

        # Imágenes personalizadas del año (opcional)
        for n, clave_img, ref_txt in [(1, 'imagen_1', 'sello pareja'), (2, 'imagen_2', 'sello individual')]:
            f = ttk.Frame(acont_frame)
            f.pack(fill='x', pady=1)
            ttk.Label(f, text=f'Imagen {n} ({ref_txt}, opcional):', width=30).pack(side='left')
            var_img = tk.StringVar()
            ttk.Entry(f, textvariable=var_img, state='readonly').pack(side='left', fill='x', expand=True)
            ttk.Button(f, text='Examinar…',
                       command=lambda n=n: self._elegir_imagen_portada(n)).pack(side='left', padx=(6, 0))
            ttk.Button(f, text='Quitar', width=7,
                       command=lambda n=n: self.campos_imagen[f'imagen_{n}'].set('')).pack(side='left', padx=(4, 0))
            self.campos_imagen[clave_img] = var_img

        ttk.Label(cont, text='Autorrellenados desde acontecimientos.csv — cámbialos si quieres. '
                              'Los "Personal" van con los sellos de las fotos (con su icono); '
                              'déjalos vacíos si no aplica. Las imágenes son opcionales: si no eliges '
                              'ninguna, se usan las de pareja/individual de siempre. Se guardan solos '
                              'para la próxima vez.',
                  foreground='#666666', font=('Helvetica', 8), wraplength=660, justify='left').pack(
            anchor='w', pady=(4, 10))

        # Carpeta de salida
        f = self._fila(cont, 'Carpeta de salida:')
        ttk.Entry(f, textvariable=self.salida_dir).pack(side='left', fill='x', expand=True, padx=(0, 6))
        ttk.Button(f, text='Examinar…', command=self._elegir_salida).pack(side='left')

        # Líneas de resumen
        f = self._fila(cont, 'Líneas de resumen:')
        ttk.Radiobutton(f, text='1 línea', variable=self.lineas_resumen, value=1).pack(side='left', padx=(0, 12))
        ttk.Radiobutton(f, text='2 líneas', variable=self.lineas_resumen, value=2).pack(side='left')

        # Escala de imagen
        f = self._fila(cont, 'Escala de imagen:')
        escala_lbl = ttk.Label(f, text='100 %', width=6)
        ttk.Scale(f, from_=90, to=115, orient='horizontal', variable=self.escala_imagen,
                  command=lambda v: escala_lbl.config(text=f'{int(float(v))} %')).pack(
            side='left', fill='x', expand=True, padx=(0, 6))
        escala_lbl.pack(side='left')
        ttk.Label(cont, text='(100% = ajuste normal; súbelo un poco si quieres que la imagen '
                              'llene más el recuadro, recortando ligeramente los bordes)',
                  foreground='#666666', font=('Helvetica', 8)).pack(anchor='w', pady=(0, 10))

        # Botones
        fb = ttk.Frame(cont)
        fb.pack(fill='x', pady=(8, 8))
        self.btn_generar = ttk.Button(fb, text='Generar álbum', command=self._on_generar)
        self.btn_generar.pack(side='left')
        self.btn_portada = ttk.Button(fb, text='Generar solo portada', command=self._on_generar_portada)
        self.btn_portada.pack(side='left', padx=(8, 0))
        self.btn_abrir = ttk.Button(fb, text='Abrir carpeta de salida', command=self._abrir_salida, state='disabled')
        self.btn_abrir.pack(side='left', padx=(8, 0))

        self.barra = ttk.Progressbar(cont, mode='indeterminate')
        self.barra.pack(fill='x', pady=(0, 10))

        # Log
        ttk.Label(cont, text='Progreso:').pack(anchor='w')
        log_frame = ttk.Frame(cont)
        log_frame.pack(fill='both', expand=True)
        self.txt_log = tk.Text(log_frame, height=14, bg='white', fg='#222222', wrap='word')
        scroll = ttk.Scrollbar(log_frame, command=self.txt_log.yview)
        self.txt_log.configure(yscrollcommand=scroll.set)
        self.txt_log.pack(side='left', fill='both', expand=True)
        scroll.pack(side='right', fill='y')

    # ------------------------------------------------------------------
    # ------------------------------------------------------------------
    def _actualizar_acontecimiento(self):
        anio_txt = self.anio.get()
        if not anio_txt.isdigit():
            return
        if not hasattr(self, 'campos_acontecimiento'):
            return
        datos = acontecimientos_mod.obtener(int(anio_txt))
        for clave, var in self.campos_acontecimiento.items():
            var.set(datos.get(clave, ''))
        for clave, var in self.campos_tipo.items():
            var.set(datos.get(clave) or 'ninguno')
        for clave, var in self.campos_imagen.items():
            var.set(datos.get(clave, ''))

    def _recoger_acontecimientos(self):
        d = {clave: var.get().strip() for clave, var in self.campos_acontecimiento.items()}
        for clave, var in self.campos_tipo.items():
            d[clave] = var.get()
        for clave, var in self.campos_imagen.items():
            d[clave] = var.get()
        return d

    def _on_generar_portada(self):
        anio_txt = self.anio.get()
        if not anio_txt.isdigit():
            messagebox.showerror('Año no válido', 'Introduce un año numérico, p. ej. 1965.')
            return
        salida_dir = self.salida_dir.get() or os.path.join(os.getcwd(), 'salida')
        os.makedirs(salida_dir, exist_ok=True)
        try:
            import portada as portada_mod
            datos = self._recoger_acontecimientos()
            acontecimientos_mod.guardar(int(anio_txt), datos)
            ruta = os.path.join(salida_dir, f'portada_{anio_txt}.pdf')
            portada_mod.construir_portada(int(anio_txt), datos, ruta)
            self._log(f'Portada generada: {ruta}')
            messagebox.showinfo('Portada generada', f'Guardada en:\n{ruta}')
            self.salida_dir.set(salida_dir)
            self.btn_abrir.config(state='normal')
        except Exception as e:
            messagebox.showerror('Error', f'No se pudo generar la portada:\n{e}')

    def _elegir_imagen_portada(self, n):
        anio_txt = self.anio.get()
        if not anio_txt.isdigit():
            messagebox.showerror('Año no válido', 'Escribe primero el año.')
            return
        ruta_origen = filedialog.askopenfilename(
            title=f'Selecciona la imagen para {anio_txt}',
            filetypes=[('Imágenes', '*.png *.jpg *.jpeg'), ('Todos los archivos', '*.*')])
        if not ruta_origen:
            return
        ext = os.path.splitext(ruta_origen)[1].lower() or '.png'
        carpeta = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'imagenes_portada')
        os.makedirs(carpeta, exist_ok=True)
        prefijo = 'imagen_fdc' if n == 'fdc' else f'imagen{n}'
        nombre_destino = f'{prefijo}_{anio_txt}{ext}'
        clave = 'imagen_fdc' if n == 'fdc' else f'imagen_{n}'
        ruta_destino = os.path.join(carpeta, nombre_destino)
        try:
            shutil.copyfile(ruta_origen, ruta_destino)
        except Exception as e:
            messagebox.showerror('Error', f'No se pudo copiar la imagen:\n{e}')
            return
        self.campos_imagen[clave].set(nombre_destino)
        self._log(f'Imagen ({clave}) de {anio_txt} guardada como {nombre_destino}')

    def _elegir_csv(self):
        ruta = filedialog.askopenfilename(title='Selecciona el CSV del catálogo',
                                           filetypes=[('CSV', '*.csv'), ('Todos los archivos', '*.*')])
        if ruta:
            self.csv_path.set(ruta)

    def _elegir_imagenes(self):
        ruta = filedialog.askdirectory(title='Selecciona la carpeta con las imágenes SPD del año')
        if ruta:
            self.imagenes_dir.set(ruta)

    def _elegir_salida(self):
        ruta = filedialog.askdirectory(title='Selecciona la carpeta de salida')
        if ruta:
            self.salida_dir.set(ruta)

    def _abrir_salida(self):
        ruta = self.salida_dir.get()
        if not os.path.isdir(ruta):
            return
        try:
            if sys.platform.startswith('win'):
                os.startfile(ruta)
            elif sys.platform == 'darwin':
                subprocess.run(['open', ruta])
            else:
                subprocess.run(['xdg-open', ruta])
        except Exception as e:
            messagebox.showwarning('Aviso', f'No se pudo abrir la carpeta automáticamente:\n{e}')

    # ------------------------------------------------------------------
    def _log(self, texto):
        self._log_queue.put(texto)

    def _procesar_cola(self):
        try:
            while True:
                linea = self._log_queue.get_nowait()
                self.txt_log.insert('end', linea + '\n')
                self.txt_log.see('end')
        except queue.Empty:
            pass
        self.after(100, self._procesar_cola)

    def _validar(self):
        if not self.csv_path.get() or not os.path.isfile(self.csv_path.get()):
            messagebox.showerror('Falta el CSV', 'Selecciona un archivo CSV de catálogo válido.')
            return False
        if not self.imagenes_dir.get() or not os.path.isdir(self.imagenes_dir.get()):
            messagebox.showerror('Falta la carpeta de imágenes', 'Selecciona una carpeta de imágenes válida.')
            return False
        if not self.anio.get().isdigit():
            messagebox.showerror('Año no válido', 'Introduce un año numérico, p. ej. 1965.')
            return False
        return True

    def _on_generar(self):
        if not self._validar():
            return
        self.btn_generar.config(state='disabled')
        self.btn_abrir.config(state='disabled')
        self.txt_log.delete('1.0', 'end')
        self.barra.start(12)

        hilo = threading.Thread(target=self._ejecutar_generacion, daemon=True)
        hilo.start()

    def _ejecutar_generacion(self):
        try:
            acontecimientos_dict = self._recoger_acontecimientos()
            info = generar(
                self.csv_path.get(),
                self.imagenes_dir.get(),
                int(self.anio.get()),
                self.salida_dir.get(),
                lineas_resumen=self.lineas_resumen.get(),
                escala_imagen=self.escala_imagen.get(),
                acontecimientos=acontecimientos_dict,
                log_fn=self._log,
            )
            self._resultado = info
        except Exception as e:
            self._log(f'ERROR: {e}')
            self._resultado = None
        finally:
            self.after(0, self._al_terminar)

    def _al_terminar(self):
        self.barra.stop()
        self.btn_generar.config(state='normal')
        if self._resultado:
            self.btn_abrir.config(state='normal')
            messagebox.showinfo('Álbum generado',
                                 f'PDF y DOCX generados en:\n{self.salida_dir.get()}')
        else:
            messagebox.showerror('No se pudo generar',
                                  'Revisa el registro de progreso para ver el detalle del error.')


if __name__ == '__main__':
    App().mainloop()
