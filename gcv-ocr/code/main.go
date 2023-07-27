package main

import (
	"encoding/json"
	gcv "gcv-ocr/api"
	"log"
	"os"

	"github.com/streadway/amqp"
)

type Message struct {
	ID     string `json:"id"`
	Text   string `json:"text"`
	Source string `json:"Source"`
}

func main() {
	conn, err := amqp.Dial(os.Getenv("RABBIT_MQ_URI"))
	if err != nil {
		log.Fatalf("Failed to connect to RabbitMQ: %s", err)
	}
	defer conn.Close()

	ch, err := conn.Channel()
	if err != nil {
		log.Fatalf("Failed to open a channel: %s", err)
	}
	defer ch.Close()

	qIn, err := ch.QueueDeclare(
		os.Getenv("INPUT_QUEUE_GCV_OCR"),
		false,
		false,
		false,
		false,
		nil,
	)
	if err != nil {
		log.Fatalf("Failed to declare a queue: %s", err)
	}

	qOut, err := ch.QueueDeclare(
		os.Getenv("INPUT_QUEUE_ANNOTATE"),
		false,
		false,
		false,
		false,
		nil,
	)
	if err != nil {
		log.Fatalf("Failed to declare a queue: %s", err)
	}

	msgs, err := ch.Consume(
		qIn.Name,
		"",
		true,
		false,
		false,
		false,
		nil,
	)
	if err != nil {
		log.Fatalf("Failed to register a consumer: %s", err)
	}

	forever := make(chan bool)

	go func() {
		for d := range msgs {
			var msg Message
			if err := json.Unmarshal(d.Body, &msg); err != nil {
				log.Printf("Failed to decode message: %s", err)
				log.Printf("Failed to decode message: %s", d.Body)
				continue
			}

			response, err := gcv.SendToOCR(msg.Text)
			if err != nil {
				log.Printf("Error running sendToOCR: %s", err)
				continue
			}

			// Extract the 'pages' and 'text' objects from the API response
			pages := response.FullTextAnnotation.Pages
			text := response.FullTextAnnotation.Text

			// Create two new messages for 'pages' and 'text'
			pageMsg := Message{
				ID:     msg.ID,
				Text:   toJSON(pages),
				Source: "gcv_ocr_pages",
			}

			textMsg := Message{
				ID:     msg.ID,
				Text:   toJSON(text),
				Source: "gcv_ocr_text",
			}

			// Publish the 'pages' and 'text' messages to the output queue
			publishMsg(ch, qOut.Name, pageMsg)
			publishMsg(ch, qOut.Name, textMsg)
		}
	}()

	log.Printf(" [*] Waiting for messages. To exit press CTRL+C")
	<-forever
}

func toJSON(v interface{}) string {
	bytes, err := json.Marshal(v)
	if err != nil {
		log.Printf("Error converting value to JSON: %v", err)
		return ""
	}
	return string(bytes)
}

func publishMsg(ch *amqp.Channel, queueName string, msg Message) {
	bytes, err := json.Marshal(msg)
	if err != nil {
		log.Printf("Failed to encode message: %s", err)
		return
	}

	err = ch.Publish(
		"",
		queueName,
		false,
		false,
		amqp.Publishing{
			ContentType: "application/json",
			Body:        bytes,
		},
	)
	if err != nil {
		log.Printf("Failed to publish a message: %s", err)
	}
}
