package main

import (
	"encoding/json"
	gpt "gpt-text-to-dwc/api"
	"log"
	"os"

	"github.com/streadway/amqp"
)

// Insert the extractDWC function from the previous response here.

// Configuration settings.
const ()

func main() {
	var rabbitMQURI = os.Getenv("RABBIT_MQ_URI")
	var apiKey = os.Getenv("GPT_API_KEY")
	var model = os.Getenv("GPT_MODEL")
	var inputQueueName = os.Getenv("INPUT_QUEUE")
	var outputQueueName = os.Getenv("OUTPUT_QUEUE")
	conn, err := amqp.Dial(rabbitMQURI)
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
		inputQueueName,
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
		outputQueueName,
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
			var ocrText string
			if err := json.Unmarshal(d.Body, &ocrText); err != nil {
				log.Printf("Failed to decode message: %s", err)
				continue
			}

			response, err := gpt.ExtractDWC(apiKey, model, &ocrText)
			if err != nil {
				log.Printf("Error running extractDWC: %s", err)
				continue
			}

			responseBytes, err := json.Marshal(response)
			if err != nil {
				log.Printf("Failed to encode response: %s", err)
				continue
			}

			err = ch.Publish(
				"",
				qOut.Name,
				false,
				false,
				amqp.Publishing{
					ContentType: "application/json",
					Body:        responseBytes,
				})
			if err != nil {
				log.Printf("Failed to publish a message: %s", err)
			}
		}
	}()

	log.Printf(" [*] Waiting for messages. To exit press CTRL+C")
	<-forever
}
