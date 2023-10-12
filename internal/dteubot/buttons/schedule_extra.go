package buttons

import (
	"errors"
	"github.com/cubicbyte/dteubot/internal/data"
	"github.com/cubicbyte/dteubot/internal/dteubot/pages"
	"github.com/cubicbyte/dteubot/internal/dteubot/settings"
	"github.com/cubicbyte/dteubot/internal/dteubot/utils"
	tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"
)

func HandleScheduleExtraButton(u *tgbotapi.Update) error {
	// Get date from button data
	button := utils.ParseButtonData(u.CallbackQuery.Data)
	date, ok := button.Params["date"]
	if !ok {
		return errors.New("no date in button data")
	}

	// Create page
	cManager := data.ChatDataManager{ChatId: u.CallbackQuery.Message.Chat.ID}
	page, err := pages.CreateScheduleExtraInfoPage(&cManager, date)
	if err != nil {
		return err
	}

	_, err = settings.Bot.Send(EditMessageRequest(page, u.CallbackQuery))
	if err != nil {
		return err
	}

	return nil
}
