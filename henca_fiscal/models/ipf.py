# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions
import odoo.addons.decimal_precision as dp
import base64
import calendar
import logging
import datetime
import hashlib
from odoo.tools import format_date

_logger = logging.getLogger(__name__)


class IpfPrinterConfig(models.Model):
    _name = "ipf.printer.config"

    def _get_ipf_type(self):
        return [("epson", "EPSON TM-T88v"), ("bixolon", "BIXOLON SRP-350")]

    name = fields.Char(string="Descripcion", required=True)
    ipf_type = fields.Selection(
        string="IPF Impresora", required=True, selection=_get_ipf_type, default="epson"
    )
    host = fields.Char(string="Host", required=True)
    user_ids = fields.Many2many(
        comodel_name="res.users", string="Usuarios", required=True
    )
    print_copy = fields.Boolean(string="Imprimir con copia", default=False)
    print_manual_copy = fields.Boolean(string="Imprimir copia manual", default=False)
    print_copy_number = fields.Integer(
        string="Numero de Copias", required=True, default=0
    )
    subsidiary = fields.Many2one(
        comodel_name="res.company", string="Sucursal", required=False
    )
    active = fields.Boolean(string="Active", default=True)
    serial = fields.Char(string="Serial de la impresora", readonly=True)
    extension = fields.Char(string="Extension LVM", default="001")
    daily_book_ids = fields.One2many(
        comodel_name="ipf.daily.book",
        inverse_name="printer_id",
        string="Libros diarios",
    )
    monthly_book_ids = fields.One2many(
        comodel_name="ipf.monthly.book",
        inverse_name="printer_id",
        string="Libros Mensuales",
    )

    def toggle_active(self):
        self.active = not self.active

    def z_close_print(self):
        pass

    def x_close_print(self):
        pass

    def start_jornada_print(self):
        pass

    def get_state(self):
        pass

    def get_advance_paper(self):
        pass

    def get_x(self):
        pass

    def get_new_shift_print(self):
        pass

    def get_printer_information(self):
        pass

    def get_cut_paper(self):
        pass

    def get_daily_book(self):
        pass

    def get_daily_book_by_date(self):
        pass

    def generate_monthly_book(self):
        pass

    def get_information_day(self):
        pass

    def get_information_shift(self):
        pass

    def get_serial(self):
        pass

    def get_user_printer(self):
        printer = self.search([("user_ids", "=", self.env.uid)])
        if printer:
            if len(printer) > 1:
                printer = printer[0]
        return printer

    def get_ipf_host(self, get_id=False):
        if self._context.get("active_model", False) == "ipf.printer.config":
            printer = self.browse(self._context["active_id"])
        else:
            printer = self.get_user_printer()

        if printer:
            if len(printer) > 1:
                printer = printer[0]

            if get_id:
                return printer.id
            else:
                return {"host": printer.host, "ipf_type": printer.ipf_type}
        else:
            raise exceptions.Warning("Las impresoras fiscales no estan configuradas!")

    def set_book_totals(self, book):
        """
        Calculate and set the totals for the given book.

        Args:
            book: The book object containing the base64 encoded data.

        Returns:
            bool: True if the book object was successfully updated, otherwise False.
        """

        # Initialize the header sums
        header_sums = [0] * 11

        # Decode the book and split it into rows
        daily_book_rows = base64.b64decode(book.book).decode("utf-8").split("\n")

        # List of indices to sum up
        indices_to_sum = [3, 4, 5, 11, 12, 14, 15, 17, 18, 20, 21]

        for row in daily_book_rows:
            fields = row.split("||")
            if fields[0] == "1":
                for i, idx in enumerate(indices_to_sum):
                    header_sums[i] += float(fields[idx]) if fields[idx] else 0.0

        # Create a dictionary to update the book
        values = {
            "doc_qty": header_sums[0],
            "total": header_sums[1],
            "total_tax": header_sums[2],
            "final_total": header_sums[3],
            "final_total_tax": header_sums[4],
            "fiscal_total": header_sums[5],
            "fiscal_total_tax": header_sums[6],
            "ncfinal_total": header_sums[7],
            "ncfinal_total_tax": header_sums[8],
            "ncfiscal_total": header_sums[9],
            "ncfiscal_total_tax": header_sums[10],
        }

        return book.write(values)

    def get_books_totals(self, daily_books):
        """
        Calculate the cumulative totals for a list of daily_books.

        Args:
            daily_books: List of daily book objects containing base64 encoded data.

        Returns:
            dict: Dictionary containing the calculated totals.
        """

        # Initialize the sums for various book headers
        header_sums = [0.0] * 16

        # List of indices to sum
        indices_to_sum = [
            3, 4, 5, 11, 12, 14, 15, 17, 18, 20, 21, 6, 7, 8, 9, 10
        ]

        for book in daily_books:
            # Decode and split the book into rows
            daily_book_rows = base64.b64decode(book.book).decode("utf-8").split("\n")

            for row in daily_book_rows:
                fields = row.split("||")
                if fields[0] == "1":
                    for i, idx in enumerate(indices_to_sum):
                        header_sums[i] += float(fields[idx]) if fields[idx] else 0.0

        # Prepare the values dictionary with conditional assignments
        values = {
            key: header_sums[i] if header_sums[i] > 0 else ""
            for i, key in enumerate([
                "doc_qty",
                "total",
                "total_tax",
                "final_total",
                "final_total_tax",
                "fiscal_total",
                "fiscal_total_tax",
                "ncfinal_total",
                "ncfinal_total_tax",
                "ncfiscal_total",
                "ncfiscal_total_tax",
                "total_tax_rate1",
                "total_tax_rate2",
                "total_tax_rate3",
                "total_tax_rate4",
                "total_tax_rate5",
            ])
        }

        return values

    def create_month_book(self, daily_books, month_total_info):
        """
        Create a monthly book summary by aggregating daily books and adding a summary line.

        Args:
            daily_books (list): List of daily book objects containing base64 encoded data.
            month_total_info (dict): Dictionary containing the month's total information.

        Returns:
            str: Monthly book summary.
        """

        # Concatenate all lines from daily books
        daily_info = "".join(
            base64.b64decode(book.book).decode("utf-8") for book in daily_books
        )

        # Create the SHA1 hash of the concatenated string
        hash_string = hashlib.sha1(bytes(daily_info, "utf-8")).hexdigest().upper()

        # Create the month resume line using f-string for readability
        month_resume_line = (
            f"3||{hash_string}||{month_total_info['doc_qty']}||{month_total_info['total']}||"
            f"{month_total_info['total_tax']}||{month_total_info['total_tax_rate1']}||"
            f"{month_total_info['total_tax_rate2']}||{month_total_info['total_tax_rate3']}||"
            f"{month_total_info['total_tax_rate4']}||{month_total_info['total_tax_rate5']}||"
            f"{month_total_info['final_total']}||{month_total_info['final_total_tax']}||"
            f"{month_total_info['fiscal_total']}||{month_total_info['fiscal_total_tax']}||"
            f"{month_total_info['ncfinal_total']}||{month_total_info['ncfinal_total_tax']}||"
            f"{month_total_info['ncfiscal_total']}||{month_total_info['ncfiscal_total_tax']}||\n"
        )

        # Create the final monthly book by appending the daily info to the month resume line
        month_book = month_resume_line + daily_info

        return month_book

    def save_book(self, new_book, serial, bookday):
        """
        Save a daily book to the database, updating or creating a new record as necessary.

        Args:
            new_book (str): The book data to save.
            serial (str): The serial number of the printer.
            bookday (str): The date for which the book is relevant, in the format 'YYYY-MM-DD'.

        Returns:
            bool: Returns True if the operation was successful.
        """

        # Get the printer ID and other relevant data
        printer_id = self.get_ipf_host(get_id=True)
        year, month, day = bookday.split("-")
        printer_config = self.get_user_printer()
        ext = printer_config.extension if printer_config.extension != "" else "000"

        # Generate the filename
        filename = f"LV{year[2:4]}{month}{day}.{ext}"

        # Search for an existing book record and delete it if found
        existing_book = self.env["ipf.daily.book"].search(
            [("printer_id", "=", printer_id), ("date", "=", bookday)]
        )
        if existing_book:
            existing_book.unlink()

        # Create a new book record
        values = {
            "printer_id": printer_id,
            "date": bookday,
            "book": base64.b64encode(new_book.encode("utf-8")),
            "serial": printer_config.serial,
            "filename": filename,
        }
        new_record = self.env["ipf.daily.book"].create(values)

        # Update the book totals
        self.set_book_totals(new_record)

        return True

    def generate_month_book(self, year, month):
        """
        Generate and save a monthly book based on daily books.

        Args:
            year (str): The year for which the monthly book is to be generated.
            month (str): The month for which the monthly book is to be generated.

        Returns:
            bool: Returns True if the monthly book is successfully generated, False otherwise.
        """

        # Get printer configuration
        printer_id = self.get_user_printer()

        # Get date information
        book_monthrange = calendar.monthrange(int(year), int(month))
        str_month = f"{int(month):02d}"
        date_choose = f"{year}{str_month}"
        first_day_month = datetime.datetime(int(year), int(month), 1)
        last_day_month = datetime.datetime(int(year), int(month), book_monthrange[1])

        # Search for daily books within the date range
        domain = [
            ("printer_id", "=", printer_id.id),
            ("date", ">=", first_day_month),
            ("date", "<=", last_day_month),
        ]
        daily_books = self.env["ipf.daily.book"].search(domain, order="date")

        if not daily_books:
            return False

        # Create monthly book
        monthly_info = self.get_books_totals(daily_books)
        month_file = self.create_month_book(daily_books, monthly_info)

        # Filename formatting
        ext = printer_id.extension if printer_id.extension else "000"
        filename = f"LVM{year}{str_month}.{ext}"

        # Search and delete any existing monthly book for the same month
        existing_book = self.env["ipf.monthly.book"].search(
            [("printer_id", "=", printer_id.id), ("date_choose", "=", date_choose)]
        )
        if existing_book:
            existing_book.unlink()

        # Create new monthly book
        values = {
            "printer_id": printer_id.id,
            "date_choose": date_choose,
            "book": base64.b64encode(month_file.encode("utf-8")),
            "serial": printer_id.serial,
            "filename": filename,
            "year": year,
            "month": format_date(self.env, last_day_month, date_format="MMMM"),
        }
        new_book = self.env["ipf.monthly.book"].create(values)

        # Remove unnecessary keys and update the new_book record
        keys_to_remove = ["total_tax_rate" + str(i) for i in range(1, 6)]
        for key in keys_to_remove:
            monthly_info.pop(key, None)

        new_book.write(monthly_info)

        return True

    @api.model
    def save_serial_printer(self, serial):
        printer_id = self.get_ipf_host(get_id=True)
        self.browse(printer_id).write({"serial": serial})
        return True


class IpfDailyBook(models.Model):
    _name = "ipf.daily.book"
    _description = "ipf daily book"
    _order = "date desc"

    printer_id = fields.Many2one("ipf.printer.config", string="Printer", readonly=True)
    subsidiary = fields.Many2one(string="Sucursal", related="printer_id.subsidiary")
    date = fields.Date("Fecha", readonly=True)
    serial = fields.Char("Serial", readonly=True)
    book = fields.Binary("Libro diario", readonly=True)
    filename = fields.Char("file name", readonly=True)
    doc_qty = fields.Integer("Transacciones", digits="Account")
    total = fields.Float("Total", digits="Account")
    total_tax = fields.Float("Total Itbis", digits="Account")
    final_total = fields.Float("Final total", digits="Account")
    final_total_tax = fields.Float("Final Itbis total", digits="Account", )
    fiscal_total = fields.Float("Fiscal total", digits="Account")
    fiscal_total_tax = fields.Float("Fiscal Itbis total", digits="Account", )
    ncfinal_total = fields.Float("NC final total", digits="Account")
    ncfinal_total_tax = fields.Float("NC final Itbis total", digits="Account", )
    ncfiscal_total = fields.Float("NC fiscal total", digits="Account")
    ncfiscal_total_tax = fields.Float("NC fiscal Itbis total", digits="Account", )


class IpfMonthlyBook(models.Model):
    _name = "ipf.monthly.book"
    _description = "ipf monthly book"
    _order = "date desc"

    printer_id = fields.Many2one("ipf.printer.config", string="Printer", readonly=True)
    subsidiary = fields.Many2one(string="Sucursal", related="printer_id.subsidiary")
    date = fields.Date(
        default=fields.Date.today(),
        string="Fecha de Generacion",
        readonly=True
    )
    serial = fields.Char("Serial", readonly=True)
    book = fields.Binary("Libro mensual", readonly=True)
    filename = fields.Char("file name", readonly=True)
    year = fields.Char("Año", readonly=True)
    month = fields.Char("Mes", readonly=True)
    date_choose = fields.Char("Fecha", readonly=True)
    doc_qty = fields.Integer("Transacciones", digits="Account")
    total = fields.Float("Total", digits="Account")
    total_tax = fields.Float("Total Itbis", digits="Account")
    final_total = fields.Float("Final total", digits="Account")
    final_total_tax = fields.Float("Final Itbis total", digits="Account", )
    fiscal_total = fields.Float("Fiscal total", digits="Account")
    fiscal_total_tax = fields.Float("Fiscal Itbis total", digits="Account", )
    ncfinal_total = fields.Float("NC final total", digits="Account")
    ncfinal_total_tax = fields.Float("NC final Itbis total", digits="Account", )
    ncfiscal_total = fields.Float("NC fiscal total", digits="Account")
    ncfiscal_total_tax = fields.Float("NC fiscal Itbis total", digits="Account", )
