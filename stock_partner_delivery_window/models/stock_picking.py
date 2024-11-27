# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import api, models
from odoo.exceptions import UserError
from odoo.tools.misc import format_datetime


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _planned_delivery_date(self):
        return self.scheduled_date

    @api.onchange("scheduled_date")
    def _onchange_scheduled_date(self):
        self.ensure_one()
        partner = self.partner_id
        anytime_delivery = partner and partner.delivery_time_preference == "anytime"
        outgoing_picking = self.picking_type_id.code == "outgoing_picking"
        # Return nothing if partner delivery preference is anytime
        if not partner or anytime_delivery or outgoing_picking:
            return
        if not partner.is_in_delivery_window(self._planned_delivery_date()):
            raise UserError(self._scheduled_date_no_delivery_window_match_msg())

    def _scheduled_date_no_delivery_window_match_msg(self):
        scheduled_date = self.scheduled_date
        formatted_scheduled_date = format_datetime(self.env, scheduled_date)
        partner = self.partner_id
        if partner.delivery_time_preference == "workdays":
            message = self.env._(
                "The scheduled date is {date} ({weekday}), but the partner is "
                "set to prefer deliveries on working days.",
                date=formatted_scheduled_date,
                weekday=scheduled_date.weekday(),
            )
        else:
            delivery_windows_strings = []
            if partner:
                for w in partner.get_delivery_windows().get(partner.id):
                    delivery_windows_strings.append(
                        f"  * {w.display_name} ({partner.tz})"
                    )
            message = self.env._(
                "The scheduled date is {date} ({tz}), but the partner is "
                "set to prefer deliveries on following time windows:\n{window}",
                date=format_datetime(self.env, self.scheduled_date),
                tz=self.env.context.get("tz"),
                window="\n".join(delivery_windows_strings),
            )
        return message
